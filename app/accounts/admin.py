from django.contrib import admin

from .models import Profile

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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = "pk", "bio", "user_verbose"
    list_display_links = "pk",
    ordering = "pk",
    search_fields = "bio",
    search_help_text = "bio"
    list_per_page = 50

    def get_queryset(self, request):
        """Оптимизация выгрузки пользователей"""
        return Profile.objects.select_related("user")

    def user_verbose(self, obj: Profile) -> str:
        """
        Отображение пользователя в административной панели в поле Profile.
        Отображать имя или username
        """
        return obj.user.first_name or obj.user.username
