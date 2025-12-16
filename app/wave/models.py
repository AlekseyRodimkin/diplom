import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from warehouse.models import Item, Place, PlaceItem, Stock

User = get_user_model()
logger = logging.getLogger(__name__)


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

    stock = models.ForeignKey(
        Stock, on_delete=models.PROTECT, related_name="waves", verbose_name="Склад"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="planned", verbose_name="Статус"
    )
    planned_date = models.DateField(verbose_name="Планируемая дата")
    actual_date = models.DateField(
        null=True, blank=True, verbose_name="Фактическая дата"
    )
    description = models.TextField(
        max_length=500, null=True, blank=True, verbose_name="Описание"
    )
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
        if (
            self.status == "completed"
            and not self.actual_date
            and (self.pk is None or Wave.objects.get(pk=self.pk).status != "completed")
        ):
            self.actual_date = timezone.now().date()

        super().save(*args, **kwargs)

    @property
    def description_short(self) -> str:
        return (
            self.description[:48] + "..."
            if self.description and len(self.description) > 48
            else (self.description or "")
        )

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

    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name="Товар", related_name="wave_items"
    )
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

    inbound_number = models.CharField(
        max_length=50, unique=True, verbose_name="Номер поставки", null=True, blank=True
    )
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Поставщик")

    class Meta:
        verbose_name = "Поставка"
        verbose_name_plural = "Поставки"
        ordering = ["-created_at"]

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Автогенерация номера поставки"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.inbound_number:
            year = timezone.now().year
            count = Inbound.objects.filter(created_at__year=year).count()
            self.inbound_number = f"INB-{year}-{count:04d}"
            super().save(update_fields=["inbound_number"])

    def get_uploads_dir(self) -> str:
        path = os.path.join(settings.MEDIA_ROOT, f"inbounds", str(self.inbound_number))
        os.makedirs(path, exist_ok=True)
        return path

    def __str__(self):
        return f"{self.inbound_number}"


class Outbound(Wave):
    """
    Модель отгрузки товаров
    Наследуется от Wave

    outbound_number: str
    recipient: str
    """

    outbound_number = models.CharField(
        max_length=50, unique=True, verbose_name="Номер отгрузки", null=True, blank=True
    )
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
            super().save(update_fields=["outbound_number"])

    def get_uploads_dir(self) -> str:
        path = os.path.join(
            settings.MEDIA_ROOT, f"outbounds", str(self.outbound_number)
        )
        os.makedirs(path, exist_ok=True)
        return path

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


ALLOWED_TRANSITIONS = {
    "planned": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
}


class InboundStatusService:

    @staticmethod
    def _validate_transition(old_status, new_status):
        """Метод валидации перехода"""
        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise ValidationError(f"Недопустимый переход: {old_status} → {new_status}")

    @staticmethod
    def _delete_inbound_place_items(inbound: Inbound):
        logger.debug(
            "InboundStatusService._delete_inbound_place_items(inb_pk:%s)", inbound.pk
        )

        inbound_place = Place.objects.get(title="INBOUND")
        item_ids = inbound.inbound_items.values_list("item_id", flat=True)
        PlaceItem.objects.filter(place=inbound_place, item_id__in=item_ids).delete()

    @staticmethod
    def _inb_items_to_inbound(inbound: Inbound):
        """Метод заселения деталей из поставки на адрес INBOUND"""
        logger.debug(
            "InboundStatusService._inb_items_to_inbound(inb_pk:%s)", inbound.pk
        )

        inbound_place = Place.objects.get(title="INBOUND")

        for ii in inbound.inbound_items.all():
            PlaceItem.objects.create(
                item=ii.item,
                place=inbound_place,
                quantity=ii.total_quantity,
                status="inbound",
            )

    @staticmethod
    def _inb_items_inbound_to_new(inbound: Inbound):
        """Метод переселения позиций поставки, заселенных с inbound на new"""
        logger.debug(
            "InboundStatusService._inb_items_inbound_to_new(inb_pk:%s)",
            inbound.pk,
        )

        new_place = Place.objects.get(title="NEW")

        items = PlaceItem.objects.filter(
            item__in=[ii.item for ii in inbound.inbound_items.all()],
            place__title="INBOUND",
        )

        for pi in items:
            pi.place = new_place
            pi.save()

    @classmethod
    def change_status(cls, *, inbound, new_status: str):
        logger.debug(
            "InboundStatusService.change_status(inb_pk:%s, new_status:%s)",
            inbound.pk,
            new_status,
        )

        old_status = inbound.status
        cls._validate_transition(old_status, new_status)

        with transaction.atomic():

            # planned -> in_progress
            if old_status == "planned" and new_status == "in_progress":
                cls._inb_items_to_inbound(inbound)

            # planned -> cancelled
            elif old_status == "planned" and new_status == "cancelled":
                pass

            # in_progress -> completed
            elif old_status == "in_progress" and new_status == "completed":
                cls._inb_items_inbound_to_new(inbound)

            # in_progress -> cancelled
            elif old_status == "in_progress" and new_status == "cancelled":
                cls._delete_inbound_place_items(inbound)

            else:
                raise ValidationError("Неподдерживаемый переход")

            inbound.status = new_status
            inbound.save(update_fields=["status"])
