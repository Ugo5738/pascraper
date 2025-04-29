import time
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from requests.exceptions import RequestException

# Import logger from THIS service
from pascraper.config.logging_config import configure_logger

# Import THIS service's model and utils
from sitescrapers.models import ScrapingJob
from sitescrapers.utils.backup import serialize_scraping_job_for_sdb

logger = configure_logger(__name__)


# --- Helper to fetch paginated data from SDB API ---
def fetch_paginated_sdb_data(api_url, id_field="primary_key", fields=None):
    """Fetches all data from a paginated SDB check endpoint."""
    data = {}
    next_url = api_url
    page_num = 1
    logger.info(f"Fetching paginated SDB data from {api_url}...")
    retrieved_count = 0

    while next_url:
        try:
            # print(f"Fetching SDB page {page_num} from {next_url}") # Verbose logging
            response = requests.get(next_url, timeout=30)  # Increased timeout
            response.raise_for_status()
            page_data = response.json()

            results = page_data.get("results", [])
            if not results:
                # print("No results in page data.")
                break  # Stop if no results on a page

            for item in results:
                key = item.get(id_field)
                if key is not None:
                    data[key] = {f: item.get(f) for f in fields} if fields else item
                    retrieved_count += 1
                else:
                    logger.warning(
                        f"Warning: SDB Item missing ID field '{id_field}': {item}"
                    )

            next_url = page_data.get("next")
            page_num += 1
            # time.sleep(0.05) # Optional delay

        except RequestException as e:
            logger.error(f"SDB API request failed for {next_url}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    f"Response status: {e.response.status_code}, Body: {e.response.text[:200]}"
                )
            return None  # Indicate failure
        except Exception as e:
            logger.error(f"Error processing paginated SDB data from {next_url}: {e}")
            return None  # Indicate failure

    logger.info(f"Finished fetching SDB data. Total records mapped: {len(data)}")
    return data


class Command(BaseCommand):
    help = "Checks ScrapingJob data consistency between Scraper service and the SDB aggregate database via APIs."

    def add_arguments(self, parser):
        parser.add_argument("--staleness-threshold-hours", type=int, default=24)
        parser.add_argument(
            "--limit", type=int, default=None, help="Limit source records checked."
        )
        parser.add_argument("--fix-missing", action="store_true")
        parser.add_argument("--fix-mismatched", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--delay", type=float, default=0.1)

    def handle(self, *args, **options):
        staleness_threshold = timedelta(hours=options["staleness_threshold_hours"])
        limit = options["limit"]
        fix_missing = options["fix_missing"]
        fix_mismatched = options["fix_mismatched"]
        dry_run = options["dry_run"]
        delay = options["delay"]

        self.stdout.write(
            self.style.SUCCESS("--- Starting Scraper Job -> SDB Consistency Check ---")
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN mode enabled."))

        # Get SDB Base URL from this service's settings
        sdb_base_url = getattr(settings, "BACKUP_SERVICE_URL", None)
        if not sdb_base_url:
            raise CommandError(
                "BACKUP_SERVICE_URL (pointing to SDB service) is not configured in Scraper settings."
            )
        sdb_base_url = sdb_base_url.rstrip("/")
        sdb_check_url = f"{sdb_base_url}/api/sdb/check/scraping-jobs/"  # Requires this endpoint in SDB
        sdb_fix_url = (
            f"{sdb_base_url}/api/sdb/scraping-job/"  # Existing endpoint in SDB
        )

        # --- Fetch Source Data (Scraper DB) ---
        self.stdout.write("Fetching data from source Scraper DB...")
        source_data = {}
        source_model = ScrapingJob
        src_pk_field = "id"
        try:
            source_qs = source_model.objects.using("default").order_by(src_pk_field)
            if limit:
                source_qs = source_qs[:limit]
            # Fetch only fields needed for comparison/fixing trigger
            source_values = source_qs.values(
                src_pk_field, "updated_at", "status"
            )  # Use 'id' as source PK
            for item in source_values.iterator():
                source_data[item[src_pk_field]] = item  # Key by source PK 'id'
            self.stdout.write(f"Fetched {len(source_data)} records from source.")
        except Exception as e:
            raise CommandError(f"Error fetching from source DB: {e}")

        if not source_data:
            self.stdout.write(
                self.style.WARNING("No source ScrapingJob records found.")
            )
            return

        # --- Fetch SDB Data via API ---
        self.stdout.write(
            f"Fetching corresponding data from SDB API: {sdb_check_url} ..."
        )
        # Ask SDB check API for primary_key (source PK) and updated_at, status
        sdb_api_fields = ["primary_key", "updated_at", "status"]
        sdb_data_raw = fetch_paginated_sdb_data(
            sdb_check_url, id_field="primary_key", fields=sdb_api_fields
        )

        if sdb_data_raw is None:
            raise CommandError(f"Failed to fetch data from SDB API {sdb_check_url}")

        self.stdout.write(f"Fetched {len(sdb_data_raw)} records from SDB API.")
        # SDB data is already keyed by primary_key (source PK)

        # --- Compare ---
        missing_in_sdb_pks = []
        mismatched_pks_to_fix = []  # For both stale update and content mismatch
        summary = {
            "source_records_checked": len(source_data),
            "sdb_records_found": len(sdb_data_raw),
            "missing_in_sdb": 0,
            "potentially_stale_or_mismatched": 0,
            "fixes_attempted_missing": 0,
            "fixes_attempted_mismatched": 0,
            "fix_api_errors": 0,
        }
        now_aware = timezone.now()

        for source_pk, source_item in source_data.items():
            sdb_item = sdb_data_raw.get(source_pk)  # Look up by source PK

            if sdb_item is None:
                summary["missing_in_sdb"] += 1
                missing_in_sdb_pks.append(source_pk)
            else:
                stale = False
                content_diff = False
                # Compare updated_at
                source_updated = source_item.get("updated_at")
                sdb_updated_str = sdb_item.get("updated_at")
                sdb_updated = None
                if sdb_updated_str:
                    try:
                        sdb_updated = parse_datetime(sdb_updated_str)
                        if sdb_updated and not sdb_updated.tzinfo:
                            sdb_updated = timezone.make_aware(
                                sdb_updated, timezone.utc
                            )  # Assume UTC if naive

                        if (
                            source_updated
                            and sdb_updated
                            and source_updated > sdb_updated
                        ):
                            # Check against threshold only if source is definitively newer
                            if (now_aware - sdb_updated) > staleness_threshold:
                                stale = True
                                self.stdout.write(
                                    f"\n  Potentially Stale Update for Scraper PK {source_pk}: Source={source_updated}, SDB={sdb_updated}"
                                )
                    except (ValueError, TypeError):
                        pass  # Ignore parsing errors

                # Compare status
                source_status = source_item.get("status")
                sdb_status = sdb_item.get("status")
                if source_status != sdb_status:
                    content_diff = True
                    self.stdout.write(
                        f"\n  Status Mismatch for Scraper PK {source_pk}: Source='{source_status}', SDB='{sdb_status}'"
                    )

                if stale or content_diff:
                    summary["potentially_stale_or_mismatched"] += 1
                    mismatched_pks_to_fix.append(source_pk)

        # --- Report & Fix ---
        can_fix = (fix_missing or fix_mismatched) and not dry_run
        if can_fix:
            self.stdout.write(self.style.WARNING("\nFixing enabled."))

        if fix_missing and missing_in_sdb_pks:
            self.stdout.write(
                self.style.WARNING(
                    f"\nAttempting to fix {summary['missing_in_sdb']} jobs missing in SDB..."
                )
            )
            for source_pk in missing_in_sdb_pks:
                if self._fix_record_api(
                    source_pk,
                    ScrapingJob,
                    serialize_scraping_job_for_sdb,
                    sdb_fix_url,
                    delay,
                    dry_run,
                ):
                    summary["fixes_attempted_missing"] += 1
                else:
                    summary["fix_api_errors"] += 1

        if fix_mismatched and mismatched_pks_to_fix:
            self.stdout.write(
                self.style.WARNING(
                    f"\nAttempting to re-sync {summary['potentially_stale_or_mismatched']} potentially mismatched/stale jobs..."
                )
            )
            for source_pk in mismatched_pks_to_fix:
                if self._fix_record_api(
                    source_pk,
                    ScrapingJob,
                    serialize_scraping_job_for_sdb,
                    sdb_fix_url,
                    delay,
                    dry_run,
                ):
                    summary["fixes_attempted_mismatched"] += 1
                else:
                    summary["fix_api_errors"] += 1

        # --- Final Summary ---
        self.stdout.write(
            self.style.SUCCESS("\n--- Scraper Job -> SDB Check Complete ---")
        )
        for key, value in summary.items():
            style = (
                self.style.SUCCESS
                if value == 0 or key.startswith("source") or key.startswith("sdb")
                else self.style.WARNING
            )
            self.stdout.write(style(f"  {key.replace('_', ' ').capitalize()}: {value}"))
        if summary["fix_api_errors"] > 0:
            self.stdout.write(
                self.style.ERROR("  Fixing API errors occurred. Check logs.")
            )

    def _fix_record_api(
        self, source_pk, SourceModel, serialize_func, sdb_fix_url, delay, dry_run
    ):
        """Fetches source record, serializes it, and POSTs to SDB API."""
        # This helper is generic now
        if dry_run:  # Skip fetch/serialize/post in dry run
            self.stdout.write(
                f"\n  [DRY RUN] Would trigger fix for PK {source_pk} -> {sdb_fix_url}"
            )
            return True

        if not sdb_fix_url or not serialize_func:
            self.stderr.write(
                self.style.ERROR(
                    f"  Cannot fix PK {source_pk}: API endpoint or serialize function not configured."
                )
            )
            return False
        try:
            # Fetch the full instance needed for serialization
            instance = SourceModel.objects.using("default").get(pk=source_pk)
            payload = serialize_func(instance)

            if payload is None:
                self.stderr.write(
                    self.style.ERROR(
                        f"  Serialization failed for PK {source_pk}. Cannot fix."
                    )
                )
                return False

            self.stdout.write(
                f"\n  Attempting POST fix for PK {source_pk} to {sdb_fix_url}..."
            )
            response = requests.post(sdb_fix_url, json=payload, timeout=30)
            response.raise_for_status()
            self.stdout.write(
                self.style.SUCCESS(
                    f"    Fix successful (Status: {response.status_code})."
                )
            )
            if delay > 0:
                time.sleep(delay)
            return True

        except SourceModel.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f"  Cannot fix PK {source_pk}: Record not found in source DB anymore."
                )
            )
            return False
        except RequestException as e:
            self.stderr.write(
                self.style.ERROR(f"  API Error fixing PK {source_pk}: {e}")
            )
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"  Fix API Response status: {e.response.status_code}")
                logger.error(f"  Fix API Response text: {e.response.text[:500]}")
            return False
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"  Unexpected error fixing PK {source_pk}: {e}")
            )
            logger.exception(f"Unexpected error fixing PK {source_pk}")
            return False
