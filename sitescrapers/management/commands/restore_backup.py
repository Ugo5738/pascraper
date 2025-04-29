import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from sitescrapers.models import ScrapingJob


class Command(BaseCommand):
    help = "Restores ScrapingJob data from the central backup service."

    def handle(self, *args, **kwargs):
        backup_url = f"{settings.BACKUP_SERVICE_URL}/api/sdb/scraping-job/"
        response = requests.get(backup_url, timeout=10)
        response.raise_for_status()
        jobs = response.json()
        for data in jobs:
            ScrapingJob.objects.update_or_create(
                pk=data["primary_key"],
                defaults={
                    "url": data["url"],
                    "source": data["source"],
                    "status": data["status"],
                    "callback_url": data.get("callback_url"),
                    "phone_number": data["phone_number"],
                    "property_id": data.get("property_id"),
                    "scraped_property_id": data.get("scraped_property_id"),
                    "task_id": data.get("task_id"),
                },
            )
        self.stdout.write(self.style.SUCCESS("Scraping jobs restored from backup."))
