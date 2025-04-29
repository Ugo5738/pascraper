# sitescrapers/management/commands/sync_jobs_to_sdb.py

import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from requests.exceptions import RequestException

# Assuming you have your logger configured
from pascraper.config.logging_config import configure_logger

# Import the source model and the refactored serializer function
from sitescrapers.models import ScrapingJob
from sitescrapers.utils.backup import serialize_scraping_job_for_sdb

logger = configure_logger(__name__)


class Command(BaseCommand):
    help = "Synchronizes existing ScrapingJob data from Scraper service to the SDB service API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of Jobs to process before logging progress.",
        )
        parser.add_argument(
            "--start-pk",
            type=int,
            default=None,
            help="Optional primary key (Scraper DB) to start processing from.",
        )
        parser.add_argument(
            "--api-url",
            type=str,
            default=None,
            help="Override the SDB API URL from settings.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the process: serialize data and log actions, but do not send API requests.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.05,  # Small delay by default
            help="Delay in seconds between API calls to avoid overwhelming the SDB service.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        start_pk = options["start_pk"]
        api_url_override = options["api_url"]
        dry_run = options["dry_run"]
        delay = options["delay"]

        # Determine the target API URL
        if api_url_override:
            sdb_api_url = (
                "https://" + api_url_override.rstrip("/") + "/api/sdb/scraping-job/"
            )

        else:
            base_url = getattr(settings, "BACKUP_SERVICE_URL", None)
            if not base_url:
                raise CommandError("BACKUP_SERVICE_URL is not configured in settings.")
            sdb_api_url = "https://" + base_url.rstrip("/") + "/api/sdb/scraping-job/"

        self.stdout.write(
            self.style.SUCCESS(
                f"--- Starting Initial ScrapingJob Sync to SDB ({sdb_api_url}) ---"
            )
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN enabled. No data will be sent.")
            )

        # Query jobs from the scraper database
        queryset = ScrapingJob.objects.using("default").all().order_by("pk")

        if start_pk:
            queryset = queryset.filter(pk__gte=start_pk)
            self.stdout.write(f"Starting processing from PK >= {start_pk}")

        total_count = queryset.count()
        self.stdout.write(f"Found {total_count} ScrapingJob records to process.")

        processed_count = 0
        success_count = 0
        error_count = 0

        # Use iterator for memory efficiency
        for job in queryset.iterator():
            processed_count += 1
            self.stdout.write(
                f"\rProcessing ScrapingJob PK={job.pk} ({processed_count}/{total_count})...",
                ending="",
            )

            try:
                # Serialize using the refactored function
                payload = serialize_scraping_job_for_sdb(job)
                if payload is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n  Skipping PK={job.pk}: Serialization failed."
                        )
                    )
                    error_count += 1
                    continue

                if dry_run:
                    if processed_count % batch_size == 0:
                        self.stdout.write(f"\n  [DRY RUN] Would sync PK={job.pk}...")
                    success_count += 1
                else:
                    # Make the actual API call
                    try:
                        response = requests.post(sdb_api_url, json=payload, timeout=30)
                        response.raise_for_status()

                        if response.status_code in [200, 201]:
                            success_count += 1
                            if processed_count % batch_size == 0:
                                self.stdout.write(
                                    f"\n  Synced batch up to PK={job.pk}. Status: {response.status_code}"
                                )
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"\n  Error for PK={job.pk}: Unexpected Status {response.status_code}"
                                )
                            )
                            logger.error(
                                f"Unexpected status {response.status_code} for ScrapingJob PK={job.pk}: {response.text[:500]}"
                            )
                            error_count += 1

                    except RequestException as e:
                        self.stdout.write(
                            self.style.ERROR(f"\n  API Error for PK={job.pk}: {e}")
                        )
                        logger.error(
                            f"Failed to sync ScrapingJob PK={job.pk}: {e}",
                            exc_info=True,
                        )
                        if hasattr(e, "response") and e.response is not None:
                            logger.error(f"  Response status: {e.response.status_code}")
                            logger.error(f"  Response text: {e.response.text[:500]}")
                        error_count += 1

                    # Optional delay
                    if delay > 0:
                        time.sleep(delay)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n  Unexpected Error processing PK={job.pk}: {e}"
                    )
                )
                logger.exception(f"Unexpected error processing ScrapingJob PK={job.pk}")
                error_count += 1

        # Final summary
        self.stdout.write(self.style.SUCCESS(f"\n--- Sync Complete ---"))
        self.stdout.write(f"Total Processed: {processed_count}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Successful Syncs{' (Dry Run)' if dry_run else ''}: {success_count}"
            )
        )
        self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING("Check application logs for details on errors.")
            )
