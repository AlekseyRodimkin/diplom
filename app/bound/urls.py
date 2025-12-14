from django.urls import path

from .views import (InboundCreateView, InboundSearchView,
                    download_inbound_docs, download_inbound_form,
                    OutboundSearchView
                    )

app_name = "bound"

urlpatterns = [
    path(
        "search/inbound/",
        InboundSearchView.as_view(),
        name="inbound-search",
    ),
    path(
        "search/outbound/",
        OutboundSearchView.as_view(),
        name="outbound-search",
    ),
    path(
        "inbound/create/",
        InboundCreateView.as_view(),
        name="inbound-create",
    ),
    # path(
    #     "outbound/create/",
    #     InboundCreateView.as_view(),
    #     name="outbound-create",
    # ),
    path("inbound/<int:pk>/docs/", download_inbound_docs, name="download_inbound_docs"),
    # path("outbound/<int:pk>/docs/", download_outbound_docs, name="download_outbound_docs"),
    path("inbound/form/", download_inbound_form, name="download_inbound_form"),
    # path("outbound/form/", download_outbound_form, name="download_outbound_form"),
]
