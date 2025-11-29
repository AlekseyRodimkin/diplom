from django.contrib.auth.models import User
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import StaffSearchForm


class StaffSearchView(LoginRequiredMixin, ListView):
    """
        Представление для поиска сотрудников

        Основная логика:
        - Добавляет форму StaffSearchForm в контекст шаблона и валидирует ей входные параметры
        - Выводит результаты постранично (100 элементов на страницу).

        Шаблон:
            staff/staff-search.html

        Поддерживаемые параметры поиска:
            работник      - частичное совпадение username / first_name / last_name / email
            group         - фильтрация по группе

        Возвращает:
            QuerySet - отфильтрованный набор ... или пустой набор
                        при отсутствии параметров запроса.
        """
    model = User
    template_name = "staff/staff-search.html"
    context_object_name = "users"
    paginate_by = 100

    def get_queryset(self):
        qs = User.objects.all()
        form = StaffSearchForm(self.request.GET)

        if not self.request.GET:
            return qs.none()

        if form.is_valid():
            data = form.cleaned_data

            if data["user"]:
                query = data["user"].strip().lower()
                qs = qs.filter(
                    Q(username__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query)
                )

            if data["group"]:
                qs = qs.filter(groups__name=data["group"])
            qs = qs.distinct()
            qs = qs.order_by('last_name', 'first_name', 'username')

        else:
            return qs.none()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StaffSearchForm(self.request.GET or None)
        user = self.request.user
        context['user_is_admin'] = user.is_superuser
        context['user_is_director'] = user.groups.filter(name='директор').exists()
        return context
