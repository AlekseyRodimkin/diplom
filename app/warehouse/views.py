from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import PlaceItem, Item, History
from .forms import PlaceItemSearchForm, ItemSearchForm, HistorySearchForm, MoveItemForm


class MainView(TemplateView):
    """
    Функция главной страницы.
    Добавляет в контекст принадлежность пользователя конкретным группам для отображения кнопок
    """
    template_name = 'warehouse/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user_is_admin'] = user.is_superuser
        context['user_is_director'] = user.groups.filter(name='директор').exists()
        return context


class InventoryLotSearchView(LoginRequiredMixin, ListView):
    """
        Представление для поиска партий товаров на складе.

        Основная логика:
        - Добавляет форму PlaceItemSearchForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результаты постранично (100 элементов на страницу).

        Шаблон:
            warehouse/lot-inventory-search.html

        Поддерживаемые параметры поиска:
            stock      - фильтрация по складу
            zone       - частичное совпадение названия зоны
            place      - частичное совпадение названия места хранения
            item_code  - частичное совпадение кода товара
            status     - точное совпадение статуса
            qty_min    - минимальное количество
            qty_max    - максимальное количество

        Возвращает:
            QuerySet - отфильтрованный набор PlaceItem или пустой набор
                        при отсутствии параметров запроса.
        """
    model = PlaceItem
    template_name = "warehouse/lot-inventory-search.html"
    context_object_name = "place_items"
    paginate_by = 100

    def get_queryset(self):
        qs = super().get_queryset().select_related('item', 'place', 'place__zone', 'place__zone__stock')
        form = PlaceItemSearchForm(self.request.GET)

        if not self.request.GET:
            return qs.none()

        if form.is_valid():
            data = form.cleaned_data
            if data.get("stock"):
                qs = qs.filter(place__zone__stock=data["stock"])
            if data.get("zone"):
                qs = qs.filter(place__zone__title__icontains=data["zone"])
            if data.get("place"):
                qs = qs.filter(place__title__icontains=data["place"])
            if data.get("item_code"):
                qs = qs.filter(item__item_code__icontains=data["item_code"])
            if data.get("status"):
                qs = qs.filter(STATUS=data["status"])
            if data.get("qty_min") is not None:
                qs = qs.filter(quantity__gte=data["qty_min"])
            if data.get("qty_max") is not None:
                qs = qs.filter(quantity__lte=data["qty_max"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PlaceItemSearchForm(self.request.GET)
        return context


class InventoryItemSearchView(LoginRequiredMixin, ListView):
    """
        Представление для поиска товаров на складе.

        Основная логика:
        - Добавляет форму PlaceItemSearchForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результаты постранично (100 элементов на страницу).

        Шаблон:
            warehouse/item-inventory-search.html

        Поддерживаемые параметры поиска:
            stock      - фильтрация по складу
            zone       - частичное совпадение названия зоны
            place      - частичное совпадение названия места хранения
            item_code  - частичное совпадение кода товара
            status     - точное совпадение статуса
            weight_min - минимальный вес
            weight_max - максимальный вес

        Возвращает:
            QuerySet - отфильтрованный набор PlaceItem или пустой набор
                        при отсутствии параметров запроса.
        """
    model = PlaceItem
    template_name = "warehouse/item-inventory-search.html"
    context_object_name = "place_items"
    paginate_by = 100

    def get_queryset(self):
        qs = super().get_queryset().select_related('item', 'place', 'place__zone', 'place__zone__stock')
        form = PlaceItemSearchForm(self.request.GET)

        if not self.request.GET:
            return qs.none()

        if form.is_valid():
            data = form.cleaned_data
            if data.get("stock"):
                qs = qs.filter(place__zone__stock=data["stock"])
            if data.get("zone"):
                qs = qs.filter(place__zone__title__icontains=data["zone"])
            if data.get("place"):
                qs = qs.filter(place__title__icontains=data["place"])
            if data.get("item_code"):
                qs = qs.filter(item__item_code__icontains=data["item_code"])
            if data.get("status"):
                qs = qs.filter(STATUS=data["status"])
            if data.get("weight_min") is not None:
                qs = qs.filter(item__weight__gte=data["weight_min"])
            if data.get("weight_max") is not None:
                qs = qs.filter(item__weight__lte=data["weight_max"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ItemSearchForm(self.request.GET)
        return context


class InventoryHistoryView(LoginRequiredMixin, ListView):
    """
        Представление для поиска истории перемещения.

        Основная логика:
        - Добавляет форму HistorySearchForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результаты постранично (100 элементов на страницу).

        Шаблон:
            warehouse/inventory-history.html

        Поддерживаемые параметры поиска:
            stock      - фильтрация по складу
            zone       - частичное совпадение названия зоны
            place      - частичное совпадение названия места хранения
            item_code  - частичное совпадение кода товара
            date       - дата
            работник   - частичное совпадение username / first_name / last_name / email

        Возвращает:
            QuerySet - отфильтрованный набор History или пустой набор
                        при отсутствии параметров запроса.
        """
    model = History
    template_name = "warehouse/inventory-history.html"
    context_object_name = "histories"
    paginate_by = 100

    def get_queryset(self):
        qs = History.objects.order_by("-date")

        # Если нет GET-параметров - показываем пусто
        if not self.request.GET:
            return qs.none()

        form = HistorySearchForm(self.request.GET)
        if not form.is_valid():
            return qs.none()

        data = form.cleaned_data

        if data["item_code"]:
            qs = qs.filter(item_code__icontains=data["item_code"].strip().upper())

            search_text = ""
            if data["stock"]:
                search_text = data["stock"].title.strip().upper()
            elif data["zone"]:
                search_text = data["zone"].strip().upper()
            elif data["place"]:
                search_text = data["place"].strip().upper()

            if search_text:
                qs = qs.filter(
                    Q(old_address__icontains=search_text) |
                    Q(new_address__icontains=search_text)
                )

            if data["user"]:
                user_query = data["user"].strip()
                qs = qs.filter(
                    Q(user__username__icontains=user_query) |
                    Q(user__first_name__icontains=user_query) |
                    Q(user__last_name__icontains=user_query) |
                    Q(user__email__icontains=user_query)
                )

            if data["date_from"]:
                qs = qs.filter(date__date__gte=data["date_from"])
            if data["date_to"]:
                qs = qs.filter(date__date__lte=data["date_to"])

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = HistorySearchForm(self.request.GET or None)
        context["total"] = self.get_queryset().count()
        return context


class InventoryMoveView(LoginRequiredMixin, View):
    """
        Представление для перемещения товара.

        Основная логика:
        - Добавляет форму MoveItemForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результат о совершении перемещения (сообщение).

        Шаблон:
            warehouse/inventory-move.html

        Поддерживаемые параметры поиска:
            item_code    - частичное совпадение кода товара
            full_address - полный адрес (Склад/Зона/Место)
            stock        - фильтрация по складу
            zone         - частичное совпадение названия зоны
            place        - частичное совпадение названия места хранения

        Возвращает:
            Перенаправление на страницу перемещения
        """
    template_name = "warehouse/inventory-move.html"

    def get(self, request):
        form = MoveItemForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = MoveItemForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                place_item = form.cleaned_data["place_item"]
                to_place = form.cleaned_data["to_place"]
                item = form.cleaned_data["item"]
                quantity = form.cleaned_data["quantity"]

                if place_item.quantity <= quantity:
                    place_item.delete()
                else:
                    place_item.quantity -= quantity
                    place_item.save()

                to_pi, created = PlaceItem.objects.get_or_create(
                    place=to_place,
                    item=item,
                    defaults={"quantity": quantity, "STATUS": "ok"}
                )
                if not created:
                    to_pi.quantity += quantity
                    to_pi.STATUS = "ok"
                to_pi.save()

                History.objects.create(
                    user=request.user,
                    item_code=item.item_code,
                    old_address=place_item.full_address,
                    new_address=to_place.full_address,
                    count=quantity,
                )

                messages.success(request, f"Товар #{item.item_code} перемещён")
                return redirect("warehouse:inventory-move")

        return render(request, self.template_name, {"form": form})
