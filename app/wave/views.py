import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView
from warehouse.models import Item, Place, PlaceItem

from .forms import (InboundCreateForm, InboundSearchForm, OutboundCreateForm,
                    OutboundSearchForm)
from .models import Inbound, InboundStatusService, Outbound
from .services import (build_zip_from_folder, create_items, create_wave,
                       parse_wave_form_file, save_file,
                       validate_and_save_wave_files)

logger = logging.getLogger(__name__)

strings_for_messages = {
    "inbound": "поставка",
    "outbound": "отгрузка",
}


class InboundSearchView(LoginRequiredMixin, ListView):
    """
    Представление для поиска поставок

    Основная логика:
    - Добавляет форму InboundSearchForm в контекст шаблона и валидирует ей входные параметры
    - Выводит результат поиска.

    Шаблон:
        wave/inbound-search.html

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
    template_name = "wave/inbound-search.html"
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
    template_name = "wave/outbound-search.html"
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
            qs = qs.filter(outbound_number__icontains=data["outbound_number"].strip())

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
        context["form"] = OutboundSearchForm(self.request.GET or None)
        context["total"] = self.get_queryset().count()

        return context


@login_required
def download_wave_docs(request, pk, wave_type) -> HttpResponse:
    """
    Функция для отдачи архива документов конкретной волны
    Получает id поставки из url
    Определяет тип волны и получает объект
    Находит волну или отдает ошибку
    Формирует архив в памяти и отдает его
    """
    if wave_type == "inbound":
        model = Inbound
        search_url = "wave:inbound-search"
    elif wave_type == "outbound":
        model = Outbound
        search_url = "wave:outbound-search"
    else:
        messages.error(request, "Некорректный тип волны")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    try:
        wave = model.objects.get(pk=pk)
    except model.DoesNotExist:
        messages.error(request, "Волна не найдена")
        return redirect(request.META.get("HTTP_REFERER", reverse_lazy(search_url)))

    buffer = build_zip_from_folder(folder_path=wave.get_uploads_dir())

    if buffer is None:
        messages.warning(request, "Документы не найдены")
        return redirect(request.META.get("HTTP_REFERER", reverse_lazy(search_url)))

    response = HttpResponse(buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{wave}.zip"'

    return response


@login_required
def download_wave_form(request, wave_type) -> HttpResponse:
    """Функция для отдачи формы"""
    if wave_type == "inbound":
        filename = "INB-FORM.xlsx"
        search_url = "wave:inbound-create"
    elif wave_type == "outbound":
        filename = "OUT-FORM.xlsx"
        search_url = "wave:outbound-create"
    else:
        messages.error(request, "Некорректный тип волны")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    file_path = os.path.join(settings.STATICFILES_DIRS[0], "forms", filename)

    if not os.path.exists(file_path):
        messages.error(request, "Ошибка c получением формы")
        logger.error("Отсутствует обязательный файл: %s", file_path)
        return redirect(request.META.get("HTTP_REFERER", reverse_lazy(search_url)))

    with open(file_path, "rb") as f:
        response = HttpResponse(
            f.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class BaseWaveCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Представление для создания волны
    Перенаправление на страницу поиска с параметрами
    """

    wave_type = None
    template_name = None
    form_file_id = None

    permission_required = [
        "wave.add_inbound",
        "wave.change_inbound",
    ]

    def post(self, request, *args, **kwargs):
        logger.debug("%sCreateView POST data: %s", self.wave_type, request.POST)
        logger.debug("%sCreateView FILES data: %s", self.wave_type, request.FILES)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        logger.error(
            "%sCreateForm invalid for user %s: errors=%s",
            self.wave_type,
            self.request.user.username,
            form.errors.as_json(),
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                wave = create_wave(
                    wave_type=self.wave_type,
                    user=self.request.user,
                    data=form.cleaned_data,
                )
                logger.debug("Created %s", wave)
                wave_dir = wave.get_uploads_dir()

                files = self.request.FILES.getlist("documents")
                if not files:
                    logger.debug("Creating %s: files not found", wave)
                else:
                    validate_and_save_wave_files(folder=wave_dir, files=files)

                form_file = self.request.FILES.get(self.form_file_id)
                if not form_file:
                    raise Exception(
                        "Файл Форма не загружен. Позиции не будут добавлены."
                    )
                file_path = save_file(folder=wave_dir, file=form_file)
                status = form.cleaned_data["status"]
                df = parse_wave_form_file(file_path=file_path, wave_type=self.wave_type)
                create_items(
                    df=df, wave=wave, status=wave.status, wave_type=self.wave_type
                )

            messages.success(
                self.request, f"Создана {strings_for_messages[self.wave_type]}: {wave}"
            )
            return redirect(
                reverse_lazy(f"wave:{self.wave_type}-search")
                + f"?stock=&{self.wave_type}_number={wave}&supplier=&status=&planned_date=&actual_date="
            )

        except Exception as e:
            logger.error("Processing error INB-FORM: %s", e)
            messages.error(self.request, f"{e}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user_is_admin"] = user.is_superuser
        context["user_is_director"] = user.groups.filter(name="director").exists()
        context["user_is_operator"] = user.groups.filter(name="operator").exists()
        return context


class InboundCreateView(BaseWaveCreateView):
    wave_type = "inbound"
    form_class = InboundCreateForm
    template_name = "wave/create-inbound.html"
    form_file_id = "inb_form"


class OutboundCreateView(BaseWaveCreateView):
    wave_type = "outbound"
    form_class = OutboundCreateForm
    template_name = "wave/create-outbound.html"
    form_file_id = "out_form"


def is_operator_or_director_or_admin(user):
    return (
        user.groups.filter(name__in=["admin", "operator", "director"]).exists()
        or user.is_superuser
    )


@login_required
@user_passes_test(is_operator_or_director_or_admin)
def inbound_change_status(request, pk):
    """Изменение статуса inbound"""
    inbound = get_object_or_404(Inbound, pk=pk)

    if request.method == "POST":
        status_value = request.POST.get("status")

        if status_value in dict(Inbound.STATUS_CHOICES):
            try:
                InboundStatusService.change_status(
                    inbound=inbound, new_status=status_value
                )
                messages.success(request, "Статус обновлён")
            except Exception as e:
                logger.exception("Ошибка при смене статуса inbound #%s: %s", pk, e)
                messages.error(request, e.messages[0])
        else:
            messages.error(request, f"Некорректный статус: {status_value}")

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("/")


@login_required
def inbound_items(request, pk):
    logger.debug("inbound_items(%s)", pk)
    inbound = Inbound.objects.prefetch_related("inbound_items__item").get(pk=pk)

    data = [
        {
            "item_code": ii.item.item_code,
            "qty": ii.total_quantity,
            "weight": ii.item.weight,
            "description": ii.item.description,
        }
        for ii in inbound.inbound_items.all()
    ]

    return JsonResponse(data, safe=False)
