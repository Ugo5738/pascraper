import requests
from celery import shared_task
from requests.exceptions import RequestException

from pascraper.config.logging_config import configure_logger
from sitescrapers.models import ScrapingJob
from utils.onthemarket.onthemarket_scraper import OnTheMarketScraper
from utils.rightmove.rightmove_scraper import RightmoveScraper
from utils.util_funcs import save_property_data, send_progress_update

logger = configure_logger(__name__)


@shared_task(name="pascraper.tasks.start_scraping_job", queue="scraper_queue")
def start_scraping_job(job_id):
    job = ScrapingJob.objects.get(id=job_id)

    try:
        # Update job status to in progress
        job.status = "in_progress"
        job.save()

        # Send progress update: Fetching details
        send_progress_update(
            job.callback_url,
            job.id,
            {
                "stage": "scraping",
                "message": "Fetching details",
                "progress": 10,
            },
        )

        # Run the appropriate scraper
        if job.source == "rightmove":
            scraper = RightmoveScraper(job.url)
        elif job.source == "onthemarket":
            scraper = OnTheMarketScraper(job.url)
        else:
            raise ValueError(f"Invalid source: {job.source}")

        # Run the scraper
        data = scraper.scrape_property()

        # Send progress update: scraping completed
        send_progress_update(
            job.callback_url,
            job.id,
            {
                "stage": "scraping",
                "message": "Fetching completed",
                "progress": 100,
            },
        )

        # Save the scraped data
        property_instance = save_property_data(data, job.source, job.url)

        # Update the job with the saved property
        job.property_id = property_instance.id
        job.status = "completed"
        job.save()

        # Send callback to the main application
        callback_data = {
            "job_id": job.id,
            "property_id": job.property_id,
            "task_id": job.task_id,
        }

        logger.info(
            f"Sending callback to URL: {job.callback_url} with data: {callback_data}"
        )

        try:
            response = requests.post(job.callback_url, json=callback_data, verify=False)
            response.raise_for_status()
            logger.info(f"Callback response status: {response.status_code}")
        except RequestException as e:
            logger.error(f"Failed to send callback: {e}")
    except Exception as e:
        # Update job status to failed
        job.status = "failed"
        job.save()

        # Optionally, send error details back via callback or logging
        send_progress_update(
            job.callback_url,
            job.id,
            {
                "stage": "error",
                "message": str(e),
                "progress": 0,
            },
        )
