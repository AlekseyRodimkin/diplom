from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import FormView, ListView
from django.db import transaction

from .forms import StructureActionForm, StructureSearchForm
from warehouse.models import Stock, Zone, Place


class StructureManagerView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
        Представление для создания-удаления склада / зоны / места.
        Требует разрешения:
        - Создание / изменение /

        Основная логика:
        - Добавляет форму StructureActionForm в контекст шаблона и валидирует ей входные параметры

        Шаблон:
            structure/structure-manager.html

        Поддерживаемые параметры поиска:
            action       - метод работы (удаление / создание)
            stock        - фильтрация по складу
            zone         - частичное совпадение названия зоны
            place        - частичное совпадение названия места хранения

        Возвращает:
            Сообщение о результате
        """
    template_name = "structure/structure-manager.html"
    form_class = StructureActionForm
    permission_required = [
        "warehouse.add_place",
        "warehouse.delete_place",
        "warehouse.change_place",
        "warehouse.add_zone",
        "warehouse.delete_zone",
        "warehouse.change_zone",
        "warehouse.add_stock",
        "warehouse.delete_stock",
        "warehouse.change_stock",
    ]

    def form_valid(self, form):
        user_display = (self.request.user.get_full_name().strip() or
                        self.request.user.username or
                        "Не определен")

        with transaction.atomic():
            action = form.cleaned_data['action']
            level = form.cleaned_data['level']

            stock_title = form.cleaned_data['stock'].strip().upper()
            zone_title = form.cleaned_data['zone'].strip().upper() if form.cleaned_data['zone'] else None
            place_title = form.cleaned_data['place'].strip().upper() if form.cleaned_data['place'] else None

            if action == 'create':
                if level == 'stock':
                    obj, created = Stock.objects.get_or_create(
                        title__iexact=stock_title,
                        defaults={
                            'title': stock_title,
                            'address': f'Склад #{stock_title} пока не имеет адреса',
                            'description': f'Склад #{stock_title} создан пользователем #{user_display}',
                        }
                    )
                    msg = f"Склад «{obj.title}» создан. Добавление адреса склада доступно через администратора"

                elif level == 'zone':
                    stock_obj = form.cleaned_data['stock_obj'] or Stock.objects.get_or_create(
                        title__iexact=stock_title,
                        defaults={
                            'title': stock_title,
                            # TODO 'address': form.cleaned_data['address'],
                            'address': f'Склад #{stock_title} пока не имеет адреса',
                            'description': f'Склад #{stock_title} создан пользователем #{user_display}',
                        }
                    )[0]
                    obj, created = Zone.objects.get_or_create(
                        stock=stock_obj,
                        title__iexact=zone_title,
                        defaults={
                            'title': zone_title,
                            'stock': stock_obj,
                            'description': f"Зона #{zone_title} создана пользователем #{user_display}"
                        }
                    )
                    msg = f"Зона «{obj.title}» создана на складе «{stock_obj.title}». Добавление адреса склада доступно через администратора"

                else:  # место
                    stock_obj = form.cleaned_data['stock_obj'] or Stock.objects.get_or_create(
                        title__iexact=stock_title,
                        defaults={
                            'title': stock_title,
                            'address': f'Склад #{stock_title} пока не имеет адреса',
                            'description': f"Склад #{stock_title} создан пользователем #{user_display}"
                        }
                    )[0]
                    zone_obj = form.cleaned_data['zone_obj'] or Zone.objects.get_or_create(
                        stock=stock_obj,
                        title__iexact=zone_title,
                        defaults={
                            'title': zone_title,
                            'stock': stock_obj,
                            'description': f"Зона #{zone_title} создана пользователем #{user_display}"
                        }
                    )[0]
                    obj, created = Place.objects.get_or_create(
                        zone=zone_obj,
                        title__iexact=place_title,
                        defaults={
                            'title': place_title,
                            'zone': zone_obj,
                            'description': f"Место #{place_title} создано пользователем #{user_display}"
                        }
                    )
                    msg = f"Место «{obj.title}» создано в зоне «{stock_obj.title}/{zone_obj.title}». Добавление адреса склада доступно через администратора"

            else:  # удаление
                if level == 'stock':
                    form.cleaned_data['stock_obj'].delete()
                    msg = f"Склад «{stock_title}» удалён"
                elif level == 'zone':
                    form.cleaned_data['zone_obj'].delete()
                    msg = f"Зона «{zone_title}» удалена"
                else:  # place
                    form.cleaned_data['place_obj'].delete()
                    msg = f"Место «{place_title}» удалено"

            messages.success(self.request, msg)
            return redirect('structure:structure-manager')


class StructureSearchView(LoginRequiredMixin, ListView):
    """
        Представление для поиска структуры склада

        Основная логика:
        - Добавляет форму StructureSearchForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результаты постранично (100 элементов на страницу).

        Шаблон:
            structure/structure-search.html

        Поддерживаемые параметры поиска:
            stock        - фильтрация по складу
            zone         - частичное совпадение названия зоны
            place        - частичное совпадение названия места хранения

        Возвращает:
            QuerySet - отфильтрованный набор Place или пустой набор
                        при отсутствии параметров запроса.
        """
    model = Place
    template_name = "structure/structure-search.html"
    context_object_name = "places"
    paginate_by = 100

    def get_queryset(self):
        qs = super().get_queryset().select_related('zone', 'zone__stock')
        form = StructureSearchForm(self.request.GET)

        if not self.request.GET:
            return qs.none()

        if form.is_valid():
            data = form.cleaned_data
            if data.get("stock"):
                qs = qs.filter(zone__stock=data["stock"])
            if data.get("zone"):
                qs = qs.filter(zone__title__icontains=data["zone"])
            if data.get("place"):
                qs = qs.filter(title__icontains=data["place"])

            qs = qs.order_by(
                'zone__stock__title',
                'zone__title',
                'title'
            )
        else:
            return qs.none()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StructureSearchForm(self.request.GET)
        return context
