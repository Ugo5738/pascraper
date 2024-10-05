import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from sitescrapers.models import Property, ScrapingJob
from utils.onthemarket.onthemarket_scraper import OnTheMarketScraper
from utils.rightmove.rightmove_scraper import RightmoveScraper
from utils.zoopla.zoopla_scraper import ZooplaScraper


class ScraperConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        url = text_data_json["url"]
        source = text_data_json["source"]

        # Create a new scraping job
        job = await self.create_scraping_job(url)

        try:
            # Update job status to in progress
            await self.update_job_status(job.id, "in_progress")

            # Run the appropriate scraper
            if source == "rightmove":
                scraper = RightmoveScraper(url)
            elif source == "zoopla":
                scraper = ZooplaScraper(url)
            elif source == "onthemarket":
                scraper = OnTheMarketScraper(url)
            else:
                raise ValueError(f"Invalid source: {source}")

            # Run the scraper
            data = await sync_to_async(scraper.scrape_property)()

            # Save the scraped data
            property_instance = await self.save_property_data(data, source, url)

            # Update the job with the saved property
            await self.update_job_property(job.id, property_instance.id)

            # Update job status to completed
            await self.update_job_status(job.id, "completed")

            # Send success message back to WebSocket
            await self.send(
                text_data=json.dumps(
                    {
                        "status": "success",
                        "message": "Scraping completed successfully",
                        "property_id": property_instance.id,
                    }
                )
            )

        except Exception as e:
            # Update job status to failed
            await self.update_job_status(job.id, "failed")

            # Send error message back to WebSocket
            await self.send(
                text_data=json.dumps({"status": "error", "message": str(e)})
            )

    @database_sync_to_async
    def create_scraping_job(self, url):
        return ScrapingJob.objects.create(url=url)

    @database_sync_to_async
    def update_job_status(self, job_id, status):
        job = ScrapingJob.objects.get(id=job_id)
        job.status = status
        job.save()

    @database_sync_to_async
    def update_job_property(self, job_id, property_id):
        job = ScrapingJob.objects.get(id=job_id)
        job.property_id = property_id
        job.save()

    @database_sync_to_async
    def save_property_data(self, data, source, url):
        return Property.objects.create(
            source=source,
            url=url,
            address=data["address"],
            price=data["price"],
            bedrooms=data["bedrooms"],
            bathrooms=data["bathrooms"],
            size=data["size"],
            house_type=data["house_type"],
            agent=data["agent"],
            description=data["description"],
            images=data["images"],
            floorplans=data["floorplans"],
        )
