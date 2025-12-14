from django import forms
from django.contrib import admin

from .models import Inbound, InboundItem, OutboundItem, Outbound

"""
Опции административной панели

list_display - отображаемые поля
list_display_links - поля-ссылки для перехода к объекту
ordering - начальная сортировка при отображении в адм. панели
search_fields - поля используемые при поиске из адм. панели
list_filter - сортировки
readonly_fields - блокировка изменяемости
search_help_text - описание поля поиска
list_per_page - кол-во строк в таблице
list_editable - изменяемые колонки


Опции связанных объектов

select_related - для связи <One to One>
class ...Inline - для связи <One to Many> и <Many to Many>
"""


@admin.register(Inbound)
class InboundAdmin(admin.ModelAdmin):
    list_display = (
        "inbound_number",
        "status",
        "stock",
        "supplier",
        "planned_date",
        "actual_date",
        "description_short",
        "updated_at",
        "created_at",
        "created_by",
    )
    ordering = ("-created_at",)
    readonly_fields = ["inbound_number", "created_by", "updated_at", "created_at"]
    search_fields = (
        "inbound_number",
        "supplier",
        "actual_date",
        "description",
    )
    search_help_text = "Номер , поставщик, дата, описание"
    list_per_page = 50


@admin.register(InboundItem)
class InboundItemAdmin(admin.ModelAdmin):
    list_display = (
        "inbound",
        "item",
        "total_quantity",
        "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 50


@admin.register(Outbound)
class OutboundAdmin(admin.ModelAdmin):
    list_display = (
        "outbound_number",
        "status",
        "stock",
        "recipient",
        "planned_date",
        "actual_date",
        "description_short",
        "updated_at",
        "created_at",
        "created_by",
    )
    ordering = ("-created_at",)
    readonly_fields = ["outbound_number", "created_by", "updated_at", "created_at"]
    search_fields = (
        "outbound_number",
        "recipient",
        "actual_date",
        "description",
    )
    search_help_text = "Номер , заказчик, дата, описание"
    list_per_page = 50


@admin.register(OutboundItem)
class OutboundItemAdmin(admin.ModelAdmin):
    list_display = (
        "outbound",
        "item",
        "total_quantity",
        "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 50
