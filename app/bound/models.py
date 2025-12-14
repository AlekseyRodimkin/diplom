from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from warehouse.models import Item, Stock

User = get_user_model()


class Wave(models.Model):
    """
    Модель волны

    pk: int
    stock: Stock
    status: str
    planned_date: datetime
    actual_date: datetime
    description: str
    created_by: User
    created_at: datetime
    updated_at: datetime
    """

    STATUS_CHOICES = [
        ("planned", "Запланирован"),
        ("in_progress", "В процессе"),
        ("completed", "Завершен"),
        ("cancelled", "Отменен"),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name="waves", verbose_name="Склад")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned", verbose_name="Статус")
    planned_date = models.DateField(verbose_name="Планируемая дата")
    actual_date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")
    description = models.TextField(max_length=500, null=True, blank=True, verbose_name="Описание")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Волна"
        verbose_name_plural = "Волны"
        ordering = ["-created_at"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Устанавливаем фактическую дату при завершении"""
        if self.status == "completed" and not self.actual_date and (
                self.pk is None or Wave.objects.get(pk=self.pk).status != "completed"):
            self.actual_date = timezone.now().date()

        super().save(*args, **kwargs)

    @property
    def description_short(self) -> str:
        return self.description[:48] + "..." if self.description and len(self.description) > 48 else (self.description or "")

    @property
    def wave_items(self):
        """Возвращает менеджер items в зависимости от подкласса"""
        if isinstance(self, Inbound):
            return self.inbound_items
        elif isinstance(self, Outbound):
            return self.outbound_items
        return self.__class__.objects.none()

    @property
    def total_items(self):
        """Общее количество позиций"""
        return self.wave_items.count()

    @property
    def total_quantity(self):
        """Общее количество товара"""
        return sum(item.total_quantity for item in self.wave_items.all())

    @property
    def is_completed(self):
        """Волна завершена"""
        return self.status == "completed"

    def __str__(self):
        return f"Wave #{self.pk}"


class WaveItem(models.Model):
    """
    Позиция волны - конкретный товар в волне

    pk: int
    total_quantity: int
    created_at: datetime
    item: Item
    """
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name="Товар", related_name="wave_items")
    total_quantity = models.PositiveIntegerField(verbose_name="Количество")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        verbose_name = "Позиция волны"
        verbose_name_plural = "Позиции волны"
        ordering = ["pk"]

    def __str__(self):
        return f"{self.item.item_code} x{self.total_quantity}"


class Inbound(Wave):
    """
    Модель поставки товаров
    Наследуется от Wave

    inbound_number: str
    supplier: str
    """

    inbound_number = models.CharField(max_length=50, unique=True, verbose_name="Номер поставки", null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Поставщик")

    class Meta:
        verbose_name = "Поставка"
        verbose_name_plural = "Поставки"
        ordering = ["-created_at"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Автогенерация номера поставки"""
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.inbound_number:
            year = timezone.now().year
            count = Inbound.objects.filter(created_at__year=year).count()
            self.inbound_number = f"INB-{year}-{count:04d}"
            super().save(update_fields=['inbound_number'])

    def __str__(self):
        return f"{self.inbound_number}"


class Outbound(Wave):
    """
    Модель отгрузки товаров
    Наследуется от Wave

    outbound_number: str
    recipient: str
    """

    outbound_number = models.CharField(max_length=50, unique=True, verbose_name="Номер отгрузки", null=True, blank=True)
    recipient = models.CharField(max_length=200, blank=True, verbose_name="Заказчик")

    class Meta:
        verbose_name = "Отгрузка"
        verbose_name_plural = "Отгрузки"
        ordering = ["-created_at"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Автогенерация номера отгрузки"""
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.outbound_number:
            year = timezone.now().year
            count = Outbound.objects.filter(created_at__year=year).count()
            self.outbound_number = f"OUT-{year}-{count:04d}"
            super().save(update_fields=['outbound_number'])

    def __str__(self):
        return f"{self.outbound_number}"


class InboundItem(WaveItem):
    """
    Позиция поставки - конкретный товар в поставке
    Наследуется от WaveItem

    pk: int
    inbound: Inbound
    total_quantity: int
    created_at: datetime
    item: Item
    """

    inbound = models.ForeignKey(
        Inbound,
        on_delete=models.CASCADE,
        related_name="inbound_items",
        verbose_name="Поставка",
    )

    class Meta:
        verbose_name = "Позиция поставки"
        verbose_name_plural = "Позиции поставки"
        ordering = ["pk"]


class OutboundItem(WaveItem):
    """
    Позиция отгрузки - конкретный товар в отгрузке
    Наследуется от WaveItem

    pk: int
    outbound: Outbound
    total_quantity: int
    created_at: datetime
    item: Item
    """

    outbound = models.ForeignKey(
        Outbound,
        on_delete=models.CASCADE,
        related_name="outbound_items",
        verbose_name="Отгрузка",
    )

    class Meta:
        verbose_name = "Позиция отгрузки"
        verbose_name_plural = "Позиции отгрузок"
        ordering = ["pk"]
