import requests
from django.conf import settings


def backup_scraping_job(instance):
    payload = {
        "primary_key": instance.pk,
        "url": instance.url,
        "source": instance.source,
        "status": instance.status,
        "callback_url": instance.callback_url,
        "phone_number": instance.phone_number,
        "property_id": instance.property_id,
        "scraped_property_id": instance.scraped_property_id,
        "task_id": instance.task_id,
        "updated_at": instance.updated_at.isoformat(),
    }
    backup_url = f"https://{settings.BACKUP_SERVICE_URL}/api/backup/scraping-job/"
    response = requests.post(backup_url, json=payload, timeout=5)
    response.raise_for_status()
