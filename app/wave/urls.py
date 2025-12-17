from django.urls import path

from .views import *

app_name = "wave"

urlpatterns = [
    path(
        "search/inbound/",
        InboundSearchView.as_view(),
        name="inbound-search",
    ),
    path(
        "inbound/create/",
        InboundCreateView.as_view(),
        name="inbound-create",
    ),
    path(
        "inbound/<int:pk>/docs/",
        download_wave_docs,
        {"wave_type": "inbound"},
        name="download_inbound_docs",
    ),
    path(
        "inbound/form/",
        download_wave_form,
        {"wave_type": "inbound"},
        name="download_inbound_form",
    ),
    path(
        "search/outbound/",
        OutboundSearchView.as_view(),
        name="outbound-search",
    ),
    path(
        "outbound/create/",
        OutboundCreateView.as_view(),
        name="outbound-create",
    ),
    path(
        "outbound/<int:pk>/docs/",
        download_wave_docs,
        {"wave_type": "outbound"},
        name="download_outbound_docs",
    ),
    path(
        "outbound/form/",
        download_wave_form,
        {"wave_type": "outbound"},
        name="download_outbound_form",
    ),
    path(
        "inbound/<int:pk>/change_status/",
        inbound_change_status,
        name="inbound_change_status",
    ),
    path("inbound/<int:pk>/items/", inbound_items, name="inbound_items"),
    path(
        "outbound/<int:pk>/change_status/",
        outbound_change_status,
        name="outbound_change_status",
    ),
    path("outbound/<int:pk>/items/", outbound_items, name="outbound_items"),
]
