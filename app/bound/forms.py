from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from warehouse.models import Stock

from .models import Inbound

# Статусы продублированы от Models.Inbound.INBOUND_STATUS_CHOICES, но без draft
INBOUND_STATUS_CHOICES = [
    ("planned", "Запланирован"),
    ("in_progress", "В процессе"),
    ("completed", "Завершен"),
    ("cancelled", "Отменен"),
]


class InboundSearchForm(forms.Form):
    """Форма на вкладке Поиск поставки"""

    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + INBOUND_STATUS_CHOICES, required=False, label="Статус"
    )

    inbound_number = forms.CharField(
        max_length=50,
        required=False,
        label="Номер поставки",
        widget=forms.TextInput(attrs={"placeholder": "INB-..."}),
    )

    supplier = forms.CharField(
        max_length=200,
        required=False,
        label="Поставщик",
        widget=forms.TextInput(attrs={"placeholder": "ИП..."}),
    )

    planned_date = forms.DateField(
        required=False,
        label="Планируемая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    actual_date = forms.DateField(
        required=False,
        label="Фактическая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )


class OutboundSearchForm(forms.Form):
    """Форма на вкладке Поиск отгрузки"""

    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + INBOUND_STATUS_CHOICES, required=False, label="Статус"
    )

    outbound_number = forms.CharField(
        max_length=50,
        required=False,
        label="Номер отгрузки",
        widget=forms.TextInput(attrs={"placeholder": "OUT-..."}),
    )

    recipient = forms.CharField(
        max_length=200,
        required=False,
        label="Заказчик",
        widget=forms.TextInput(attrs={"placeholder": "ИП..."}),
    )

    planned_date = forms.DateField(
        required=False,
        label="Планируемая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    actual_date = forms.DateField(
        required=False,
        label="Фактическая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )


# Статусы продублированы от Models.Inbound.INBOUND_STATUS_CHOICES, без Завершен и Отменен
SECOND_INBOUND_STATUS_CHOICES = [
    ("planned", "Запланирован"),
    ("in_progress", "В процессе"),
    ("completed", "Завершен"),
    ("cancelled", "Отменен"),
]


# Для отправки файлов как часть формы

# class MultipleFileInput(forms.ClearableFileInput):
#     allow_multiple_selected = True
#
# class MultipleFileField(forms.FileField):
#     def __init__(self, *args, **kwargs):
#         kwargs.setdefault("widget", MultipleFileInput())
#         super().__init__(*args, **kwargs)
#
#     def clean(self, data, initial=None):
#         single_file_clean = super().clean
#         if isinstance(data, (list, tuple)):
#             result = [single_file_clean(d, initial) for d in data]
#         else:
#             result = single_file_clean(data, initial)
#         return result


class InboundCreateForm(forms.Form):
    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=True, label="Склад"
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + SECOND_INBOUND_STATUS_CHOICES,
        required=True,
        label="Статус",
    )
    supplier = forms.CharField(
        max_length=200,
        required=True,
        label="Поставщик",
        widget=forms.TextInput(attrs={"placeholder": "ИП Иванов А.Б."}),
    )
    planned_date = forms.DateField(
        required=True,
        label="Планируемая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    actual_date = forms.DateField(
        required=False,
        label="Фактическая дата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    description = forms.CharField(
        max_length=500,
        label="Описание",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control form-control-sm",
                "rows": 4,
                "placeholder": "Введите описание",
            }
        ),
    )

    # Для отправки файлов как часть формы
    # documents = MultipleFileField(label='Select files', required=False)

    def clean_supplier(self):
        """
        Валидируем supplier
        - Минимальная длинна строки 5 символов
        """
        supplier = self.cleaned_data.get("supplier").strip().upper()
        if len(supplier) < 4:
            raise ValidationError("Название поставщика слишком короткое")
        return supplier

    def clean(self):
        """
        ("planned", "Запланирован"),
        ("in_progress", "В процессе"),
        ("completed", "Завершен"),
        ("cancelled", "Отменен"),
        """
        cleaned = super().clean()

        planned_date = cleaned.get("planned_date")
        actual_date = cleaned.get("actual_date")
        status = cleaned.get("status")

        # Фактическая дата может быть раньше планируемой

        # Незавершенная поставка не может иметь фактическую дату
        if status in ("planned", "in_progress", "cancelled") and actual_date:
            raise ValidationError(
                "Незавершенная поставка не может иметь фактическую дату"
            )

        # Завершенная поставка должна иметь фактическую дату
        if status == "completed" and actual_date is None:
            raise ValidationError("Завершенная поставка должна иметь фактическую дату")

        return cleaned
