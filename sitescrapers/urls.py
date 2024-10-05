from django.urls import path
from sitescrapers.views import OnTheMarketAPIView, RightmoveAPIView, ZooplaAPIView

urlpatterns = [
    path("rightmove/", RightmoveAPIView.as_view(), name="rightmove_api"),
    path("zoopla/", ZooplaAPIView.as_view(), name="zoopla_api"),
    path("onthemarket/", OnTheMarketAPIView.as_view(), name="onthemarket_api"),
]
