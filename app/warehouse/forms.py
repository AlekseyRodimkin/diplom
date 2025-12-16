from django import forms

from .models import Item, Place, PlaceItem, Stock, Zone

# Статусы продублированы от Models.PlaceItem.STATUS_CHOICES
PLACE_ITEM_STATUS_CHOICES = [
    ("inbound", "inbound"),
    ("outbound", "outbound"),
    ("blk", "block"),
    ("new", "new"),
    ("ok", "ok"),
]


class PlaceItemSearchForm(forms.Form):
    """Форма поиска на вкладке Поиск Партии"""

    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    zone = forms.CharField(
        max_length=100,
        required=False,
        label="Зона",
        widget=forms.TextInput(attrs={"placeholder": "Зона", "class": "form-control"}),
    )
    place = forms.CharField(
        max_length=100,
        required=False,
        label="Место",
        widget=forms.TextInput(attrs={"placeholder": "Место", "class": "form-control"}),
    )
    item_code = forms.CharField(
        max_length=100,
        required=False,
        label="Код товара",
        widget=forms.TextInput(
            attrs={"placeholder": "Код товара", "class": "form-control"}
        ),
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + PLACE_ITEM_STATUS_CHOICES,
        required=False,
        label="Статус",
    )
    qty_min = forms.IntegerField(
        required=False,
        min_value=1,
        label="Кол-во мин",
        widget=forms.NumberInput(
            attrs={"placeholder": "Кол-во мин", "class": "form-control"}
        ),
    )
    qty_max = forms.IntegerField(
        required=False,
        min_value=1,
        label="Кол-во макс",
        widget=forms.NumberInput(
            attrs={"placeholder": "Кол-во макс", "class": "form-control"}
        ),
    )


class ItemSearchForm(forms.Form):
    """Форма поиска на вкладке Поиск товара"""

    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    zone = forms.CharField(
        max_length=100,
        required=False,
        label="Зона",
        widget=forms.TextInput(attrs={"placeholder": "Зона", "class": "form-control"}),
    )
    place = forms.CharField(
        max_length=100,
        required=False,
        label="Место",
        widget=forms.TextInput(attrs={"placeholder": "Место", "class": "form-control"}),
    )
    item_code = forms.CharField(
        max_length=100,
        required=False,
        label="Код товара",
        widget=forms.TextInput(
            attrs={"placeholder": "Код товара", "class": "form-control"}
        ),
    )
    status = forms.ChoiceField(
        choices=[("", "---")] + PLACE_ITEM_STATUS_CHOICES, required=False
    )
    weight_min = forms.IntegerField(
        required=False,
        min_value=1,
        label="Вес мин г",
        widget=forms.NumberInput(
            attrs={"placeholder": "Вес мин г", "class": "form-control"}
        ),
    )
    weight_max = forms.IntegerField(
        required=False,
        min_value=1,
        label="Вес макс г",
        widget=forms.NumberInput(
            attrs={"placeholder": "Вес макс г", "class": "form-control"}
        ),
    )


class HistorySearchForm(forms.Form):
    """Форма поиска на вкладке История перемещений"""

    stock = forms.ModelChoiceField(
        queryset=Stock.objects.all(), required=False, label="Склад"
    )
    zone = forms.CharField(
        max_length=100,
        required=False,
        label="Зона",
        widget=forms.TextInput(attrs={"placeholder": "Зона", "class": "form-control"}),
    )
    place = forms.CharField(
        max_length=100,
        required=False,
        label="Место",
        widget=forms.TextInput(attrs={"placeholder": "Место", "class": "form-control"}),
    )
    item_code = forms.CharField(
        max_length=100,
        required=False,
        label="Код товара",
        widget=forms.TextInput(
            attrs={"placeholder": "Код товара", "class": "form-control"}
        ),
    )
    date_from = forms.DateField(
        required=False,
        label="Дата от",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    date_to = forms.DateField(
        required=False,
        label="Дата до",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    user = forms.CharField(
        max_length=150,
        required=False,
        label="Работник",
        widget=forms.TextInput(
            attrs={"placeholder": "Работник", "class": "form-control"}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Дата «от» не может быть позже «до»")
        return cleaned_data


class MoveItemForm(forms.Form):
    """Форма на вкладке Перемещение товара"""

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.request:
            instance._current_user = self.request.user
        if commit:
            instance.save()
        return instance

    # блок откуда ------------------------------------------------
    item_code = forms.CharField(
        max_length=100,
        required=True,
        label="Код товара",
        widget=forms.TextInput(
            attrs={"placeholder": "Код товара", "class": "form-control"}
        ),
    )
    from_stock = forms.ModelChoiceField(
        required=False,
        queryset=Stock.objects.all(),
        label="Склад",
    )
    from_zone = forms.CharField(
        max_length=100,
        required=False,
        label="Зона",
        widget=forms.TextInput(attrs={"placeholder": "Зона", "class": "form-control"}),
    )
    from_place = forms.CharField(
        max_length=100,
        required=False,
        label="Место",
        widget=forms.TextInput(attrs={"placeholder": "Место", "class": "form-control"}),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Количество",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "style": "width: 100px;"}
        ),
    )
    from_full_address = forms.CharField(
        max_length=100,
        required=False,
        label="Полный адрес",
        widget=forms.TextInput(attrs={"placeholder": "1/A/1", "class": "form-control"}),
    )

    # блок куда ------------------------------------------------
    to_stock = forms.ModelChoiceField(
        required=False,
        queryset=Stock.objects.all(),
        label="Склад",
    )
    to_zone = forms.CharField(
        max_length=100,
        required=False,
        label="Зона",
        widget=forms.TextInput(attrs={"placeholder": "Зона", "class": "form-control"}),
    )
    to_place = forms.CharField(
        max_length=100,
        required=False,
        label="Место",
        widget=forms.TextInput(attrs={"placeholder": "Место", "class": "form-control"}),
    )
    to_full_address = forms.CharField(
        max_length=100,
        required=False,
        label="Полный адрес",
        widget=forms.TextInput(attrs={"placeholder": "1/A/1", "class": "form-control"}),
    )

    def clean(self):
        """Дополнительная валидация форм"""
        cleaned_data = super().clean()

        item_code = cleaned_data.get("item_code").strip().upper()
        quantity = cleaned_data.get("quantity")
        from_full_address = cleaned_data.get("from_full_address").strip().upper()
        from_stock = cleaned_data.get("from_stock")
        from_zone = cleaned_data.get("from_zone").strip().upper()
        from_place = cleaned_data.get("from_place").strip().upper()
        to_full_address = cleaned_data.get("to_full_address").strip().upper()
        to_stock = cleaned_data.get("to_stock")
        to_zone = cleaned_data.get("to_zone").strip().upper()
        to_place = cleaned_data.get("to_place").strip().upper()

        if not item_code:
            raise forms.ValidationError("Введите код товара")

        try:
            item = Item.objects.get(item_code=item_code)
        except Item.DoesNotExist:
            raise forms.ValidationError("Товар с таким кодом не найден")

        # откуда
        if from_full_address:
            from_place = self._place_from_full_address(from_full_address)
        else:
            from_place = self._place_from_parts(
                stock=from_stock, zone=from_zone, place=from_place
            )

        if not from_place:
            raise forms.ValidationError("Не удалось определить место ОТКУДА")

        # куда
        if to_full_address:
            to_place = self._place_from_full_address(to_full_address)
        else:
            to_place = self._place_from_parts(
                stock=to_stock, zone=to_zone, place=to_place
            )

        if not to_place:
            raise forms.ValidationError("Не удалось определить место КУДА")

        if from_place == to_place:
            raise forms.ValidationError("Товар остался там же")

        try:
            place_item = PlaceItem.objects.get(place=from_place, item=item)
            if place_item.quantity < quantity:
                raise forms.ValidationError(
                    f"Недостаточно товара: есть {place_item.quantity} шт."
                )
        except PlaceItem.DoesNotExist:
            raise forms.ValidationError("Товара нет на указанном месте ОТКУДА")

        cleaned_data["item"] = item
        cleaned_data["from_place"] = from_place
        cleaned_data["to_place"] = to_place
        cleaned_data["place_item"] = place_item

        return cleaned_data

    def _place_from_full_address(self, address: str):
        """Парсит полный адрес Склад/Зона/Место или Зона/Место или Место"""
        parts = [p.strip() for p in address.split("/") if p.strip()]
        if not parts:
            return None

        place_title = parts[-1]
        zone_title = parts[-2] if len(parts) >= 2 else None
        stock_title = parts[0] if len(parts) >= 3 else None

        return self._find_place(
            stock_title=stock_title, zone_title=zone_title, place_title=place_title
        )

    def _place_from_parts(self, stock=None, zone=None, place=None):
        if not place:
            return None
        return self._find_place(stock=stock, zone_title=zone, place_title=place)

    def _find_place(
        self, stock=None, stock_title=None, zone_title=None, place_title=None
    ):
        """Универсальный поиск места"""
        if not place_title:
            return None

        qs = Place.objects.all()

        if stock:
            qs = qs.filter(zone__stock=stock)
        if stock_title:
            qs = qs.filter(zone__stock__title__icontains=stock_title)
        if zone_title:
            qs = qs.filter(zone__title__icontains=zone_title)
        if place_title:
            qs = qs.filter(title__icontains=place_title)

        try:
            return qs.get()
        except Place.DoesNotExist:
            return None
        except Place.MultipleObjectsReturned:
            return qs.filter(title__iexact=place_title.strip()).first()
