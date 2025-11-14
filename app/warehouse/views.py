from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import PlaceItem
from .forms import PlaceItemSearchForm


def main(request: HttpRequest) -> HttpResponse:
    return render(request, "warehouse/main.html")


class InventoryLotView(LoginRequiredMixin, ListView):
    model = PlaceItem
    template_name = "warehouse/inventory-lot.html"
    context_object_name = "place_items"
    paginate_by = 100

    def get_queryset(self):
        qs = super().get_queryset().select_related('item', 'place', 'place__zone', 'place__zone__stock')
        form = PlaceItemSearchForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            if data.get("stock"):
                qs = qs.filter(place__zone__stock=data["stock"])
            if data.get("zone"):
                qs = qs.filter(place__zone=data["zone"])
            if data.get("place"):
                qs = qs.filter(place=data["place"])
            if data.get("item_code"):
                qs = qs.filter(item__item_code__icontains=data["item_code"])
            if data.get("status"):
                qs = qs.filter(STATUS=data["status"])
            if data.get("weight_min") is not None:
                qs = qs.filter(item__weight__gte=data["weight_min"])
            if data.get("weight_max") is not None:
                qs = qs.filter(item__weight__lte=data["weight_max"])
            if data.get("qty_min") is not None:
                qs = qs.filter(quantity__gte=data["qty_min"])
            if data.get("qty_max") is not None:
                qs = qs.filter(quantity__lte=data["qty_max"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PlaceItemSearchForm(self.request.GET)
        return context
