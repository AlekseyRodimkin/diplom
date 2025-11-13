from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Item(models.Model):
    """
    Модель товара

    pk: int
    weight: int: 1 < weight < 100.000.000
    item_code: str: len(item_code) <= 100
    description: str: len(description) <= 500
    created_at: datetime: 2000-01-02 10:30:45.123456+00:00
    """
    weight = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
    )
    item_code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def description_short(self) -> str:
        return self.description if len(self.description) < 48 else self.description[:48] + "..."

    class Meta:
        ordering = ["item_code"]

    #     indexes = [
    #         models.Index(fields=['item_code', 'created_at']),
    #     ]
    #     # verbose_name = "Товар"
    #     # verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.item_code}"


class Place(models.Model):
    """
    Модель места

    pk: int
    title: str: len(address) <= 100
    description: str: len(description) <= 500
    created_at: datetime: 2000-01-02 10:30:45.123456+00:00
    zone: Zone
    """
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    zone = models.ForeignKey(
        "Zone",
        on_delete=models.CASCADE,
        related_name="places",
        null=True,
        blank=True,
    )

    @property
    def description_short(self) -> str:
        return self.description if len(self.description) < 48 else self.description[:48] + "..."

    class Meta:
        ordering = ["title"]

    #     indexes = [
    #         models.Index(fields=['title', ]),
    #     ]

    def __str__(self):
        return f"{self.title}"


class PlaceItem(models.Model):
    """
    Промежуточная таблица: товар на конкретном адресе

    pk: int
    place: Place
    item: Item
    quantity: int
    """
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="place_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="place_items")
    quantity = models.PositiveIntegerField(default=1)
    STATUSES_CHOICES = [
        ("ok", "normal"),
        ("blk", "block"),
        ("no", "absent"),
        ("new", "new"),
        ("dock", "registration"),
    ]

    STATUS = models.CharField(
        max_length=20,
        choices=STATUSES_CHOICES,
        default="new",
    )

    class Meta:
        ordering = ["pk"]
        unique_together = ("place", "item")  # Один товар не может дублироваться в одном месте

    def __str__(self):
        return f"{self.item.item_code} x{self.quantity} @ {self.place.title}"


class Zone(models.Model):
    """
    Модель зоны

    pk: int
    title: str: len(address) <= 100
    description: str: len(description) <= 500
    created_at: datetime: 2000-01-02 10:30:45.123456+00:00
    stock: Stock
    """
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.ForeignKey(
        "Stock",
        on_delete=models.CASCADE,
        related_name="zones",
        null=True,
        blank=True,
    )

    @property
    def description_short(self) -> str:
        return self.description if len(self.description) < 48 else self.description[:48] + "..."

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title}"


class Stock(models.Model):
    """
    Модель склада

    pk: int
    title: str: len(address) <= 100
    address: str: len(address) <= 300
    description: str: len(description) <= 500
    created_at: datetime: 2000-01-02 10:30:45.123456+00:00
    """
    title = models.CharField(max_length=100)
    address = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def description_short(self) -> str:
        return self.description if len(self.description) < 48 else self.description[:48] + "..."

    class Meta:
        ordering = ["pk"]

    #     indexes = [
    #         models.Index(fields=['title', 'address', 'created_at']),
    #     ]

    def __str__(self):
        return f"{self.title}"
