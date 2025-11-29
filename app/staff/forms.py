from django import forms

GROUP_CHOICES = [
    ("admin", "Администратор"),
    ("director", "Директор"),
    ("master", "Мастер"),
    ("worker", "Рабочий"),
]


class StaffSearchForm(forms.Form):
    """Форма на вкладке Поиск персонала"""
    user = forms.CharField(
        max_length=100,
        required=False,
        label="Работник",
        widget=forms.TextInput(attrs={"placeholder": "Работник", "class": "form-control"})
    )
    group = forms.ChoiceField(choices=[("", "---")] + GROUP_CHOICES, required=False, label="Группа")
