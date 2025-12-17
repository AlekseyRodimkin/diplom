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
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.outbound_number:
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
    def _planned_to_in_progress(inbound: Inbound):
        logger.debug(
            "InboundStatusService._planned_to_in_progress(inb_pk:%s)", inbound.pk
        )
        # получаем адрес inbound
        inbound_place = Place.objects.get(title="INBOUND")

        # создание заселения деталей из поставки на адрес INBOUND
        for inbound_item in inbound.inbound_items.all():
            PlaceItem.objects.create(
                item=inbound_item.item,
                place=inbound_place,
                quantity=inbound_item.total_quantity,
                status="inbound",
            )

    @staticmethod
    def _in_progress_to_completed(inbound: Inbound):
        logger.debug(
            "InboundStatusService._in_progress_to_completed(inb_pk:%s)", inbound.pk
        )
        # получаем места с товарами из поставки на адресе inbound
        place_items = PlaceItem.objects.filter(
            item__in=[inbound_item.item for inbound_item in inbound.inbound_items.all()],
            place__title="INBOUND",
        )

        # получаем место new
        new_place = Place.objects.get(title="NEW")

        # меняем адрес у заселесений (переселение) c inbound на new
        for place_item in place_items:
            place_item.place = new_place
            place_item.save()

    @staticmethod
    def _in_progress_to_cancelled(inbound: Inbound):
        logger.debug(
            "InboundStatusService._in_progress_to_cancelled(inb_pk:%s)",
            inbound.pk,
        )
        # получение id item из поставки
        item_ids = inbound.inbound_items.values_list("item_id", flat=True)
        # получаем адрес inbound
        inbound_place = Place.objects.get(title="INBOUND")
        # удаление PlaceItem с местом inbound и товарами поставки
        PlaceItem.objects.filter(place=inbound_place, item_id__in=item_ids).delete()

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
            # создать заселение деталей поставки на inbound
            if old_status == "planned" and new_status == "in_progress":
                cls._planned_to_in_progress(inbound)


            # planned -> cancelled
            elif old_status == "planned" and new_status == "cancelled":
                pass

            # in_progress -> completed
            # получаем все PlaceItem с товарами из поставки (InboundItems) и адресом inbound
            # получаем место new
            # переселяем заселения поставки с inbound на new
            elif old_status == "in_progress" and new_status == "completed":
                cls._in_progress_to_completed(inbound)


            # in_progress -> cancelled
            # получаем id товаров поставки
            # получаем адрес inbound
            # удаляем места с ними и адресом inbound
            elif old_status == "in_progress" and new_status == "cancelled":
                cls._in_progress_to_cancelled(inbound)


            else:
                raise ValidationError("Неподдерживаемый переход")

            inbound.status = new_status
            inbound.save(update_fields=["status"])


class OutboundStatusService:

    @staticmethod
    def _validate_transition(old_status, new_status):
        """Метод валидации перехода"""
        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise ValidationError(f"Недопустимый переход: {old_status} → {new_status}")

    @staticmethod
    def _planned_to_in_progress(outbound: Outbound):
        logger.debug("OutboundStatusService._planned_to_in_progress(out_pk:%s)", outbound.pk)

        outbound_place = Place.objects.get(title="OUTBOUND")

        for outbound_item in outbound.outbound_items.all():
            item = outbound_item.item
            quantity_needed = outbound_item.total_quantity
            storage_items = PlaceItem.objects.filter(item=item, status="ok").order_by("id")

            # всего можем снять с адресов
            total_available = sum(place_item.quantity for place_item in storage_items)

            if total_available < quantity_needed:
                raise ValidationError(
                    f"Недостаточно {item} на складе: требуется {quantity_needed}, доступно {total_available}")

            remaining_needed = quantity_needed  # осталось необходимо
            for place_item in storage_items:

                if remaining_needed <= 0:
                    break

                if place_item.quantity <= remaining_needed:  # если товара на адресе <= кол-ва для снятия
                    remaining_needed -= place_item.quantity  # осталось - на адресе
                    place_item.delete()  # удаляем адрес

                else:
                    place_item.quantity -= remaining_needed
                    remaining_needed = 0
                    place_item.save()

            PlaceItem.objects.create(
                item=item,
                place=outbound_place,
                quantity=quantity_needed,
                status="outbound",
            )

    @staticmethod
    def _in_progress_to_completed(outbound: Outbound):
        logger.debug(
            "OutboundStatusService._in_progress_to_completed(out_pk:%s)", outbound.pk
        )
        # получаем адрес outbound
        outbound_place = Place.objects.get(title="OUTBOUND")

        # получаем id товаров из отгрузки
        item_ids = outbound.outbound_items.values_list("item_id", flat=True)

        # удаляем места с адресом outbound и деталями из отгрузки
        PlaceItem.objects.filter(place=outbound_place, item_id__in=item_ids).delete()

    @staticmethod
    def _in_progress_to_cancelled(outbound: Outbound):
        logger.debug(
            "OutboundStatusService._in_progress_to_cancelled(out_pk:%s)", outbound.pk
        )
        # получаем адрес new и OUTBOUND
        new_place = Place.objects.get(title="NEW")
        outbound_place = Place.objects.get(title="OUTBOUND")

        # получаем места с товарами из отгрузки и адресом outbound
        place_items = PlaceItem.objects.filter(
            item__in=[outbound_item.item for outbound_item in outbound.outbound_items.all()],
            place=outbound_place,
        )

        for place_item in place_items:
            existing, created = PlaceItem.objects.get_or_create(
                place=new_place,
                item=place_item.item,
                defaults={'quantity': 0, 'status': 'ok'}
            )
            existing.quantity += place_item.quantity
            existing.status = 'ok'
            existing.save()

            place_item.delete()

    @classmethod
    def change_status(cls, *, outbound, new_status: str):
        logger.debug(
            "OutboundStatusService.change_status(out_pk:%s, new_status:%s)",
            outbound.pk,
            new_status,
        )

        old_status = outbound.status
        cls._validate_transition(old_status, new_status)

        with transaction.atomic():

            # planned -> in_progress
            if old_status == "planned" and new_status == "in_progress":
                cls._planned_to_in_progress(outbound)

            # planned -> cancelled
            elif old_status == "planned" and new_status == "cancelled":
                pass

            # in_progress -> completed
            # получаем адрес outbound
            # получаем id товаров из отгрузки
            # удаляем места с адресом outbound и деталями из отгрузки
            elif old_status == "in_progress" and new_status == "completed":
                cls._in_progress_to_completed(outbound)


            # in_progress -> cancelled
            # получаем адрес new
            # получаем места с товарами из отгрузки и адресом outbound
            # меняем адрес у заселений на new
            elif old_status == "in_progress" and new_status == "cancelled":
                cls._in_progress_to_cancelled(outbound)


            else:
                raise ValidationError("Неподдерживаемый переход")

            outbound.status = new_status
            outbound.save(update_fields=["status"])
