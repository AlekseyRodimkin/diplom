from django.contrib.auth.views import LoginView
from django.urls import path

from .views import main, InventoryLotView

app_name = "warehouse"

urlpatterns = [
    path("", main, name="main"),
    path("inventory/lot", InventoryLotView.as_view(), name="lot-inventory-search"),
]
