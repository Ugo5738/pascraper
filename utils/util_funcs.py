import re
from decimal import Decimal

import requests

from pascraper.config.logging_config import configure_logger
from sitescrapers.models import Property

logger = configure_logger(__name__)


def save_property_data(data, source, url):
    try:
        # Clean and convert the price
        price_str = data["price"]
        # Remove currency symbols and commas
        price_str = re.sub(r"[^\d.]", "", price_str)
        # Convert to Decimal
        price = Decimal(price_str) if price_str else None

        property_instance, created = Property.objects.update_or_create(
            url=url,
            defaults={
                "source": source,
                "address": data.get("address"),
                "price": price,
                "bedrooms": data.get("bedrooms"),
                "bathrooms": data.get("bathrooms"),
                "size": data.get("size"),
                "house_type": data.get("house_type"),
                "agent": data.get("agent"),
                "description": data.get("description"),
                "images": data.get("images"),
                "floorplans": data.get("floorplans"),
            },
        )

        if created:
            logger.info(f"New property created with ID: {property_instance.id}")
        else:
            logger.info(f"Existing property updated with ID: {property_instance.id}")

        return property_instance
    except Exception as e:
        logger.info(f"Error saving property data: {str(e)}")
        raise


def send_progress_update(callback_url, job_id, progress_data):
    try:
        response = requests.post(
            callback_url,
            json={
                "job_id": job_id,
                "progress": progress_data,
            },
        )
        response.raise_for_status()
        logger.info(f"Progress update sent: {progress_data}")
    except requests.RequestException as e:
        logger.error(f"Failed to send progress update: {e}")
