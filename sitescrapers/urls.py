from django.urls import path

from sitescrapers import views

urlpatterns = [
    path("rightmove/", views.RightmoveAPIView.as_view(), name="rightmove_api"),
    path("zoopla/", views.ZooplaAPIView.as_view(), name="zoopla_api"),
    path("onthemarket/", views.OnTheMarketAPIView.as_view(), name="onthemarket_api"),
    path("scrape/", views.StartScrapingView.as_view(), name="start-scraping"),
    path(
        "scrape/<int:job_id>/data/",
        views.ScrapingJobDataView.as_view(),
        name="scraping-job-data",
    ),
]
