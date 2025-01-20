from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from sitescrapers.models import Property, ScrapingJob
from sitescrapers.tasks import start_scraping_job
from utils.onthemarket.onthemarket_scraper import OnTheMarketScraper
from utils.rightmove.rightmove_scraper import RightmoveScraper
from utils.zoopla.zoopla_scraper import ZooplaScraper


class RightmoveAPIView(APIView):
    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": "URL parameter is required"}, status=400)
        scraper = RightmoveScraper(url)
        data = scraper.scrape_property()
        return JsonResponse(data, status=status.HTTP_200_OK)


class ZooplaAPIView(APIView):
    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": "URL parameter is required"}, status=400)
        scraper = ZooplaScraper(url)
        data = scraper.scrape()
        return JsonResponse(data, status=status.HTTP_200_OK)


class OnTheMarketAPIView(APIView):
    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": "URL parameter is required"}, status=400)
        scraper = OnTheMarketScraper(url)
        data = scraper.scrape()
        return JsonResponse(data, status=status.HTTP_200_OK)


class StartScrapingView(APIView):
    def post(self, request):
        url = request.data.get("url")
        source = request.data.get("source")
        callback_url = request.data.get("callback_url")
        property_id = request.data.get("property_id")
        task_id = request.data.get("task_id")
        phone_number = request.data.get("phone_number")

        if not url or not source or not callback_url or not phone_number:
            return Response(
                {"error": "URL, source, callback_url and phone_number are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = ScrapingJob.objects.create(
            url=url,
            source=source,
            callback_url=callback_url,
            property_id=property_id,
            task_id=task_id,
            phone_number=phone_number,
        )

        start_scraping_job.delay(job.id)

        return Response({"job_id": job.id}, status=status.HTTP_202_ACCEPTED)


class ScrapingJobDataView(APIView):
    def get(self, request, job_id):
        try:
            job = ScrapingJob.objects.get(id=job_id)
            if job.status != "completed":
                return Response(
                    {"error": "Scraping not completed yet."},
                    status=status.HTTP_202_ACCEPTED,
                )
            property_instance = Property.objects.get(id=job.scraped_property_id)
            property_data = {
                "address": property_instance.address,
                "price": str(property_instance.price),
                "bedrooms": property_instance.bedrooms,
                "bathrooms": property_instance.bathrooms,
                "size": property_instance.size,
                "house_type": property_instance.house_type,
                "agent": property_instance.agent,
                "description": property_instance.description,
                "time_on_market": property_instance.time_on_market,
                "features": property_instance.features,
                "listing_type": property_instance.listing_type,
                "images": property_instance.images,
                "floorplans": property_instance.floorplans,
            }
            return Response({"data": property_data})
        except ScrapingJob.DoesNotExist:
            return Response(
                {"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found."}, status=status.HTTP_404_NOT_FOUND
            )


class StandaloneScrapeView(APIView):
    """
    This endpoint performs a one-time scrape of a given URL
    and returns the data immediately, without scheduling a job or using Celery.
    """

    def post(self, request, *args, **kwargs):
        """
        POST /scrape-once/
        Body params:
            {
                "url": "https://www.rightmove.co.uk/properties/12345678",
                "source": "rightmove"  # Optional if you want to handle logic
            }
        """
        url = request.data.get("url")
        source = request.data.get("source", "rightmove")

        if not url:
            return Response(
                {"error": "URL is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) Choose the appropriate scraper based on `source` or fallback
        if source.lower() == "rightmove":
            scraper = RightmoveScraper(url)
        elif source.lower() == "zoopla":
            scraper = ZooplaScraper(url)
        elif source.lower() == "onthemarket":
            scraper = OnTheMarketScraper(url)
        else:
            # You could auto-detect or handle default logic here
            # For simplicity, defaulting to RightmoveScraper as an example
            scraper = RightmoveScraper(url)

        try:
            # 2) Scrape data synchronously
            scraped_data = scraper.scrape_property()  # or `.scrape()` if Zoopla

            # # 3) (Optional) Save the data to Property model
            # property_instance = save_property_data(scraped_data, source, url)

            # 4) Return the scraped data directly to the client
            return Response(
                {
                    "message": "Scrape successful.",
                    "scraped_data": scraped_data,
                    # "property_id": property_instance.id,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
