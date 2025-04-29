# sitescrapers/utils/backup.py
import requests
from django.conf import settings

from pascraper.config.logging_config import configure_logger

logger = configure_logger(__name__)


def serialize_scraping_job_for_sdb(instance):
    """Serializes a sitescrapers.ScrapingJob instance for the SDB service."""
    if not instance:
        return None

    payload = {
        "primary_key": instance.pk,  # Send the source PK as 'primary_key'
        "url": instance.url,
        "source": instance.source,
        "status": instance.status,
        "callback_url": instance.callback_url,
        "phone_number": instance.phone_number,
        # These IDs reference records in the Orchestration DB, send them as is
        "property_id": instance.property_id,
        "task_id": instance.task_id,
        # This ID references a record in the Scraper DB's Property table
        "scraped_property_id": instance.scraped_property_id,
        # SDB model handles its own timestamps on save
        # "updated_at": instance.updated_at.isoformat(),
    }
    return payload


def backup_scraping_job(instance):
    """Sends the serialized scraping job data to the SDB service."""
    payload = serialize_scraping_job_for_sdb(instance)
    if not payload:
        logger.warning(f"Could not serialize ScrapingJob PK={instance.pk} for backup.")
        return

    # Construct the correct URL for the SDB scraping job endpoint
    try:
        base_url = settings.BACKUP_SERVICE_URL.rstrip("/")
        sdb_job_url = f"{base_url}/api/sdb/scraping-job/"
    except AttributeError:
        logger.error(
            "BACKUP_SERVICE_URL not configured in settings. Cannot backup scraping job."
        )
        return  # Exit if URL isn't set

    logger.debug(
        f"Sending scraping job backup payload for PK={instance.pk} to {sdb_job_url}"
    )
    try:
        response = requests.post(sdb_job_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(
            f"Successfully backed up ScrapingJob PK={instance.pk}. Status: {response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to backup ScrapingJob PK={instance.pk}: {e}", exc_info=True
        )
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"SDB Response Status: {e.response.status_code}")
            logger.error(f"SDB Response Body: {e.response.text[:500]}...")
