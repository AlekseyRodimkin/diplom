import io
import logging
import os
import zipfile

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView
from warehouse.models import Item, Place, PlaceItem

from .forms import InboundCreateForm, InboundSearchForm, OutboundSearchForm
from .models import Inbound, InboundItem, Outbound

logger = logging.getLogger(__name__)


def file_save(folder: str, file) -> str | None:
    """Функция сохранения файла"""
    try:
        filename = os.path.basename(file.name)
        file_path = os.path.join(folder, filename)
        logger.debug(
            "file_save(folder=%s, file=%s): filename=%s, file_path=%s",
            folder,
            file,
            filename,
            file_path,
        )
        with open(file_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        return file_path
    except Exception as e:
        logger.error(e)


class InboundSearchView(LoginRequiredMixin, ListView):
    """
    Представление для поиска поставок

    Основная логика:
    - Добавляет форму InboundSearchForm в контекст шаблона и валидирует ей входные параметры
    - Выводит результат поиска.

    Шаблон:
        bound/inbound-search.html

    Поддерживаемые параметры поиска:
        stock          - фильтрация по складу
        status         - фильтрация по статусу
        inbound_number - частичное совпадение номера поставки
        supplier       - частичное совпадение поставщика
        planned_date   - фильтрация по >= плановой дате поставки
        actual_date    - фильтрация по <= фактической дате поставки

    Возвращает:
        QuerySet - отфильтрованный набор Inbound или пустой набор
                    при отсутствии параметров запроса.
    """

    model = Inbound
    template_name = "bound/inbound-search.html"
    context_object_name = "inbounds"
    paginate_by = 100
    ordering = ["-planned_date", "-created_at"]

    def get_queryset(self):
        qs = Inbound.objects.select_related("stock").all()

        if not self.request.GET:
            return qs.none()

        form = InboundSearchForm(self.request.GET)
        if not form.is_valid():
            return qs.none()

        data = form.cleaned_data

        if data["stock"]:
            qs = qs.filter(stock=data["stock"])

        if data["inbound_number"]:
            qs = qs.filter(inbound_number__icontains=data["inbound_number"].strip())

        if data["supplier"]:
            qs = qs.filter(supplier__icontains=data["supplier"].strip())

        if data["status"]:
            qs = qs.filter(status=data["status"])

        if data["planned_date"]:
            qs = qs.filter(planned_date__gte=data["planned_date"])

        if data["actual_date"]:
            qs = qs.filter(actual_date__lte=data["actual_date"])

        qs = qs.order_by("-inbound_number")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user_is_admin"] = user.is_superuser
        context["user_is_director"] = user.groups.filter(name="director").exists()
        context["user_is_operator"] = user.groups.filter(name="operator").exists()
        context["form"] = InboundSearchForm(self.request.GET or None)
        context["total"] = self.get_queryset().count()

        return context


class OutboundSearchView(LoginRequiredMixin, ListView):
    """
    Представление для поиска Отгрузок

    Основная логика:
    - Добавляет форму OutboundSearchForm в контекст шаблона и валидирует ей входные параметры
    - Выводит результат поиска.

    Шаблон:
        bound/inbound-search.html

    Поддерживаемые параметры поиска:
        stock          - фильтрация по складу
        status         - фильтрация по статусу
        outbound_number - частичное совпадение номера отгрузки
        recipient       - частичное совпадение заказчика
        planned_date   - фильтрация по >= плановой дате отгрузки
        actual_date    - фильтрация по <= фактической дате отгрузки

    Возвращает:
        QuerySet - отфильтрованный набор Outbound или пустой набор
                    при отсутствии параметров запроса.
    """

    model = Outbound
    template_name = "bound/outbound-search.html"
    context_object_name = "outbounds"
    paginate_by = 100
    ordering = ["-planned_date", "-created_at"]

    def get_queryset(self):
        qs = Outbound.objects.select_related("stock").all()

        if not self.request.GET:
            return qs.none()

        form = OutboundSearchForm(self.request.GET)
        if not form.is_valid():
            return qs.none()

        data = form.cleaned_data

        if data["stock"]:
            qs = qs.filter(stock=data["stock"])

        if data["outbound_number"]:
            qs = qs.filter(inbound_number__icontains=data["outbound_number"].strip())

        if data["recipient"]:
            qs = qs.filter(supplier__icontains=data["recipient"].strip())

        if data["status"]:
            qs = qs.filter(status=data["status"])

        if data["planned_date"]:
            qs = qs.filter(planned_date__gte=data["planned_date"])

        if data["actual_date"]:
            qs = qs.filter(actual_date__lte=data["actual_date"])

        qs = qs.order_by("-outbound_number")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user_is_admin"] = user.is_superuser
        context["user_is_director"] = user.groups.filter(name="director").exists()
        context["user_is_operator"] = user.groups.filter(name="operator").exists()
        context["form"] = InboundSearchForm(self.request.GET or None)
        context["total"] = self.get_queryset().count()

        return context


@login_required
def download_inbound_docs(request, pk) -> HttpResponse:
    """
    Функция для отдачи архива документов конкретной поставки

    Получает id поставки из url
    Находит поставку или отдает ошибку
    Находит папку по inbound_number или возвращает сообщение об отсутствии документов
    Формирует архив в памяти и отдает его
    """
    try:
        inbound = Inbound.objects.get(pk=pk)
    except Inbound.DoesNotExist:
        messages.error(request, "Поставка не найдена")
        return redirect(
            request.META.get(
                "HTTP_REFERER", reverse_lazy("bound:inbound-inventory-search")
            )
        )

    inb_num = str(inbound.inbound_number)
    folder = os.path.join(settings.MEDIA_ROOT, "inbounds", inb_num)

    if not os.path.isdir(folder):
        messages.warning(request, "Документы отсутствуют")
        return redirect(
            request.META.get("HTTP_REFERER", reverse_lazy("bound:inbound-search"))
        )

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if os.path.isfile(file_path):
                zip_file.write(file_path, arcname=filename)

    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{inb_num}.zip"'

    return response


@login_required
def download_inbound_form(request) -> HttpResponse:
    """Отдаёт файл INB-FORM.xlsx"""

    file = os.path.join(settings.MEDIA_ROOT, "INB-FORM.xlsx")

    if not os.path.exists(file):
        messages.warning(request, "Ошибка c получением формы поставки")
        logger.error("Отсутствует обязательный файл: %s", file)
        return redirect(
            request.META.get("HTTP_REFERER", reverse_lazy("bound:inbound-create"))
        )

    with open(file, "rb") as f:
        response = HttpResponse(
            f.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="INB-FORM.xlsx"'
        return response


class InboundCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Представление для создания поставки

    Шаблон:
        bound/create-inbound.html

    Поддерживаемые параметры:
        stock: Stock
        status: str
        supplier: str
        planned_date: datetime
        actual_date: datetime

    Возвращает:
        Перенаправление на страницу поиска поставок с параметрами для отображения созданной поставки


    Логика создания Inbound

    1 - Если статус 'Запланировано'
        - Создаются объекты 'Item' c атрибутами:
            item_code: из формы xlsx
            weight: из формы xlsx
            description: из формы xlsx

        - Создается 'Inbound' без 'actual_date' со всеми атрибутами и статусом 'planned':
            'actual_date' будет являться 'None' при незавершенной поставке ( clean() в InboundCreateForm )

        - Создаются объекты 'InboundItem' с атрибутами:
            Item
            Inbound

    2 - Если статус 'Отменено'
        - Создается 'Inbound' с 'actual_date' со всеми атрибутами и статусом 'cancelled':
            'actual_date' будет передана ( clean() в InboundCreateForm )

    3 - Если статус 'В прогрессе'
        - Создаются объекты 'Item' c атрибутами:
            item_code: из формы xlsx
            weight: из формы xlsx
            description: из формы xlsx

        - Создается 'Inbound' без 'actual_date' со всеми атрибутами и статусом 'in_progress':
            'actual_date' будет являться 'None' при незавершенной поставке ( clean() в InboundCreateForm )

        - Создаются объекты 'PlaceItem' (детали селятся) с атрибутами:
            place: inbound
            STATUS: inbound
            item: Item
            quantity: count из формы xlsx

    4 - Если статус 'Завершено'
        - Создаются объекты 'Item' c атрибутами:
            item_code: из формы xlsx
            weight: из формы xlsx
            description: из формы xlsx

        - Создается 'Inbound' с 'actual_date' со всеми атрибутами и статусом 'completed':
            'actual_date' будет передана ( clean() в InboundCreateForm )

        - Создаются объекты 'InboundItem' с атрибутами:
            Item
            Inbound

        - Создаются объекты 'PlaceItem' (детали селятся) с атрибутами:
            place: new
            STATUS: new
            item: Item
            quantity: count из формы xlsx
    """

    template_name = "bound/create-inbound.html"
    form_class = InboundCreateForm

    permission_required = [
        "bound.add_inbound",
        "bound.change_inbound",
    ]

    def get(self, request, *args, **kwargs):
        logger.debug(
            "InboundCreateView visited by %s (%s)",
            request.user.username,
            request.user.id,
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.debug("InboundCreateView POST data: %s", request.POST)
        logger.debug("InboundCreateView FILES data: %s", request.FILES)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.error(
            "InboundCreateForm invalid for user %s: errors=%s",
            self.request.user.username,
            form.errors.as_json(),
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        status = form.cleaned_data["status"]
        try:
            with transaction.atomic():
                inbound = Inbound.objects.create(
                    stock=form.cleaned_data["stock"],
                    status=form.cleaned_data["status"],
                    supplier=form.cleaned_data["supplier"].upper().strip(),
                    planned_date=form.cleaned_data["planned_date"],
                    actual_date=form.cleaned_data["actual_date"],
                    description=form.cleaned_data["description"],
                    created_by=self.request.user.username,
                )
                logger.debug("Created inbound %s", inbound.inbound_number)

                folder = os.path.join(
                    settings.MEDIA_ROOT, "inbounds", str(inbound.inbound_number)
                )
                os.makedirs(folder, exist_ok=True)
                logger.debug("Creating %s: files found", inbound.inbound_number)

                # Для отправки файлов как часть формы
                # files = form.cleaned_data['documents']
                files = self.request.FILES.getlist("documents")
                if files:
                    for file in files:
                        if file.size > settings.MAX_FILE_SIZE:
                            raise Exception(
                                f"Файл {file.name} слишком большой (макс. {settings.MAX_FILE_SIZE / (1024 * 1024)} МБ)."
                            )

                        ext = os.path.splitext(file.name)[1].lower()
                        if ext not in settings.ALLOWED_EXTS_DOCS:
                            raise Exception(f"Недопустимое расширение для: {file.name}")

                    for file in files:
                        file_save(folder=folder, file=file)

                else:
                    logger.debug("Creating %s: files not found", inbound.inbound_number)

                if status == "cancelled":
                    logger.debug("Created %s", inbound.inbound_number)
                    messages.success(
                        self.request, f"Создана поставка: {inbound.inbound_number}"
                    )
                    return redirect(
                        reverse_lazy("bound:inbound-search")
                        + "?stock=&inbound_number={num}&supplier={sup}&status={stat}&planned_date={date}&actual_date=".format(
                            num=inbound.inbound_number,
                            sup=form.cleaned_data["supplier"].upper().strip(),
                            stat=form.cleaned_data["status"],
                            date=form.cleaned_data["planned_date"],
                        )
                    )

                inb_file = self.request.FILES.get("inb_form")
                if not inb_file:
                    raise Exception(
                        "Файл INB-FORM не загружен. Товары не будут добавлены."
                    )

                file_path = file_save(folder=folder, file=inb_file)

                ext = os.path.splitext(inb_file.name)[1].lower()
                if ext in {".xlsx", ".xls"}:
                    df = pd.read_excel(file_path, header=0, dtype=str)
                elif ext == ".csv":
                    df = pd.read_csv(file_path, header=0, dtype=str)
                else:
                    raise Exception("Неподдерживаемый формат файла INB-FORM")

                df = (
                    df.astype(str)
                    .replace(["nan", "NaN", "None", "<NA>"], "")
                    .apply(lambda x: x.str.strip())
                )

                required_cols = {"Партномер", "Вес г", "Количество", "Описание"}
                if not required_cols.issubset(df.columns):
                    missing = required_cols - set(df.columns)
                    raise Exception(
                        f"В файле INB-FORM отсутствуют колонки: {', '.join(missing)}"
                    )

                inbound_place = Place.objects.filter(title="INBOUND").first()
                if not inbound_place:
                    raise Exception(
                        f"На складе #{inbound.stock.title} отсутствует технический адрес #INBOUND"
                    )

                new_place = Place.objects.filter(title="NEW").first()
                if status == "completed" and not new_place:
                    raise Exception(
                        f"На складе #{inbound.stock.title} отсутствует технический адрес #NEW"
                    )

                validation_errors = []
                for index, row in df.iterrows():
                    item_code = str(row["Партномер"]).strip().upper()
                    if not item_code:
                        continue

                    weight_str = row.get("Вес г", "").strip()
                    quantity_str = row.get("Количество", "0").strip()

                    try:
                        if weight_str:
                            int(weight_str)
                        int(quantity_str)
                    except ValueError:
                        validation_errors.append(
                            f"Строка {index + 2}: неверный формат веса или количества для {item_code} "
                            f"(вес='{weight_str}', количество='{quantity_str}')"
                        )

                if validation_errors:
                    for err in validation_errors:
                        messages.error(self.request, err)
                    raise Exception("Валидация INB-FORM не пройдена")

                created_items = 0
                for _, row in df.iterrows():
                    item_code = str(row["Партномер"]).strip().upper()
                    if not item_code:
                        continue

                    weight_str = row.get("Вес г", "").strip()
                    quantity_str = row.get("Количество", "0").strip()
                    description_str = row.get("Описание", "").strip()

                    weight = int(weight_str) if weight_str else None
                    quantity = int(quantity_str)

                    item, created = Item.objects.get_or_create(
                        item_code=item_code,
                        defaults={"weight": weight, "description": description_str},
                    )
                    if created:
                        created_items += 1

                    InboundItem.objects.get_or_create(
                        item=item, inbound=inbound, total_quantity=quantity
                    )

                    if status == "in_progress":
                        PlaceItem.objects.get_or_create(
                            item=item,
                            quantity=quantity,
                            status="inbound",
                            place=inbound_place,
                        )
                    elif status == "completed":
                        PlaceItem.objects.get_or_create(
                            item=item,
                            quantity=quantity,
                            status="new",
                            place=new_place,
                        )

                messages.success(
                    self.request,
                    f"Добавлено новых товаров: {created_items}. Всего строк: {len(df)}",
                )

                messages.success(
                    self.request, f"Создана поставка: {inbound.inbound_number}"
                )
                return redirect(
                    reverse_lazy("bound:inbound-search")
                    + f"?stock=&inbound_number={inbound.inbound_number}&supplier={form.cleaned_data['supplier'].upper().strip()}&status={status}&planned_date={form.cleaned_data['planned_date']}&actual_date="
                )

        except Exception as e:
            logger.error("Processing error INB-FORM: %s", e)
            messages.error(self.request, f"Ошибка: {e}")
            if "inbound" in locals():
                inbound.delete()
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user_is_admin"] = user.is_superuser
        context["user_is_director"] = user.groups.filter(name="director").exists()
        context["user_is_operator"] = user.groups.filter(name="operator").exists()
        return context
