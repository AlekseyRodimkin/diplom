from django import forms
from .models import Stock, Zone, Place, Item

STATUS_CHOICES = [
    ("ok", "ok"),
    ("blk", "blk"),
    ("no", "no"),
    ("new", "new"),
    ("dock", "dock"),
]


class PlaceItemSearchForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=Stock.objects.all(), required=False)
    zone = forms.ModelChoiceField(queryset=Zone.objects.all(), required=False)
    place = forms.ModelChoiceField(queryset=Place.objects.all(), required=False)
    item_code = forms.CharField(max_length=100, required=False)
    status = forms.ChoiceField(choices=[("", "---")] + STATUS_CHOICES, required=False)
    weight_min = forms.IntegerField(required=False, min_value=1)
    weight_max = forms.IntegerField(required=False, min_value=1)
    qty_min = forms.IntegerField(required=False, min_value=0)
    qty_max = forms.IntegerField(required=False, min_value=0)
