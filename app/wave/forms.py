from django import forms
from django.core.exceptions import ValidationError
from warehouse.models import Stock

WAVE_STATUS_CHOICES = [
    ("planned", "Запланирован"),
    ("in_progress", "В процессе"),
    ("completed", "Завершен"),
    ("cancelled", "Отменен"),
]


class WaveSearchForm(forms.Form):
    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + WAVE_STATUS_CHOICES, required=False, label="Статус"
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


class InboundSearchForm(WaveSearchForm):
    """Форма на вкладке Поиск поставки"""

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


class OutboundSearchForm(WaveSearchForm):
    """Форма на вкладке Поиск отгрузки"""

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


class WaveCreateForm(forms.Form):
    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=True, label="Склад"
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + WAVE_STATUS_CHOICES,
        required=True,
        label="Статус",
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


class InboundCreateForm(WaveCreateForm):
    supplier = forms.CharField(
        max_length=200,
        required=True,
        label="Поставщик",
        widget=forms.TextInput(attrs={"placeholder": "ИП Иванов А.Б."}),
    )

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


class OutboundCreateForm(WaveCreateForm):
    recipient = forms.CharField(
        max_length=200,
        required=True,
        label="Заказчик",
        widget=forms.TextInput(attrs={"placeholder": "ИП Иванов А.Б."}),
    )

    def clean_supplier(self):
        """
        Валидируем recipient
        - Минимальная длинна строки 5 символов
        """
        recipient = self.cleaned_data.get("recipient").strip().upper()
        if len(recipient) < 4:
            raise ValidationError("Название заказчика слишком короткое")
        return recipient

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

        # Незавершенная отгрузка не может иметь фактическую дату
        if status in ("planned", "in_progress", "cancelled") and actual_date:
            raise ValidationError(
                "Незавершенная отгрузка не может иметь фактическую дату"
            )

        # Завершенная отгрузка должна иметь фактическую дату
        if status == "completed" and actual_date is None:
            raise ValidationError("Завершенная отгрузка должна иметь фактическую дату")

        return cleaned
