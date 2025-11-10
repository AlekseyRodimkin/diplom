from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = "pk", "bio", "user_verbose"
    list_display_links = []
    ordering = "pk",
    search_fields = []

    def get_queryset(self, request):
        """Оптимизация выгрузки пользователей"""
        return Profile.objects.select_related("user")

    def user_verbose(self, obj: Profile) -> str:
        """
        Отображение пользователя в административной панели в поле Profile.
        Отображать имя или username
        """
        return obj.user.first_name or obj.user.username
