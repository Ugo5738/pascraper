from django.urls import path
from sitescrapers import consumers

websocket_urlpatterns = [
    path("ws/scraper/", consumers.ScraperConsumer.as_asgi()),
]
