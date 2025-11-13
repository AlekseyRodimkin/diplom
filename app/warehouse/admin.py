from django.contrib import admin
from django import forms

from .models import Item, Place, Zone, Stock, PlaceItem

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


class PlaceItemInline(admin.TabularInline):
    model = PlaceItem
    extra = 0
    autocomplete_fields = ["item"]


class PlaceInline(admin.TabularInline):
    model = Place
    extra = 0
    autocomplete_fields = ["zone"]


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0
    autocomplete_fields = ["stock"]


class StockAdminForm(forms.ModelForm):
    zones = forms.ModelMultipleChoiceField(
        queryset=Zone.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Zones", is_stacked=False)
    )

    class Meta:
        model = Stock
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["zones"].initial = self.instance.zones.all()

    def save(self, commit=True):
        stock = super().save(commit=False)
        if commit:
            stock.save()
        if stock.pk:
            self.instance.zones.update(stock=None)
            self.cleaned_data["zones"].update(stock=stock)
        return stock


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = "pk", "item_code", "weight", "description_short", "created_at",
    list_display_links = "pk", "item_code",
    ordering = "item_code", "pk",
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]
    search_fields = "item_code", "description",
    search_help_text = "item_code , description"
    list_per_page = 50


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = "pk", "title", "description_short", "created_at",
    list_display_links = "pk", "title",
    ordering = "title", "pk",
    inlines = [PlaceItemInline]
    list_filter = ["zone", "created_at"]
    readonly_fields = ["created_at"]
    search_fields = "title", "description",
    search_help_text = "title , description"
    list_per_page = 50


@admin.register(PlaceItem)
class PlaceItemAdmin(admin.ModelAdmin):
    list_display = "pk", "place", "item", "quantity", "STATUS"
    list_display_links = "pk",
    ordering = "pk",
    autocomplete_fields = "place", "item",
    search_fields = "place__title", "item__item_code", "quantity",
    search_help_text = "place__title , item__item_code, quantity"
    list_editable = ("STATUS",)
    list_per_page = 50


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = "pk", "title", "description_short", "created_at",
    list_display_links = "pk", "title",
    ordering = "title", "pk",
    inlines = [PlaceInline]
    list_filter = ["stock"]
    readonly_fields = ["created_at"]
    search_fields = "title", "description",
    search_help_text = "title , description"
    list_per_page = 50


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = "pk", "title", "address", "description_short", "created_at",
    list_display_links = "pk", "title",
    ordering = "title", "pk",
    inlines = [ZoneInline]
    form = StockAdminForm
    readonly_fields = ["created_at"]
    search_fields = "title", "address", "description",
    search_help_text = "title , address, description"
    list_per_page = 50
