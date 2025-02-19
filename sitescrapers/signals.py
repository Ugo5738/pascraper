from django.db.models.signals import post_save
from django.dispatch import receiver

from sitescrapers.models import ScrapingJob
from sitescrapers.utils.backup import backup_scraping_job


@receiver(post_save, sender=ScrapingJob)
def scraping_job_saved(sender, instance, **kwargs):
    try:
        backup_scraping_job(instance)
    except Exception as e:
        # Log or handle the error as needed
        print("Error backing up ScrapingJob:", e)
