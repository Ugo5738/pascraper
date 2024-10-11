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

        if not url or not source or not callback_url:
            return Response(
                {"error": "URL, source, and callback_url are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = ScrapingJob.objects.create(
            url=url,
            source=source,
            callback_url=callback_url,
            property_id=property_id,
            task_id=task_id,
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
            property_instance = Property.objects.get(id=job.property_id)
            property_data = {
                "address": property_instance.address,
                "price": str(property_instance.price),
                "bedrooms": property_instance.bedrooms,
                "bathrooms": property_instance.bathrooms,
                "size": property_instance.size,
                "house_type": property_instance.house_type,
                "agent": property_instance.agent,
                "description": property_instance.description,
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
