from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
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


# if any part fails, what happens, does it reach out to us
