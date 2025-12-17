import logging
from wave.models import InboundItem, OutboundItem

from django.db import transaction
from django.db.models import Sum
from warehouse.models import Item, Place, PlaceItem

logger = logging.getLogger(__name__)


def create_items_by_inb_form(
    df, wave_status, inbound_place, new_place
) -> list[tuple[Item, int]]:
    """
    валидация полей формы
    создание объектов Item
    При статусе in_progress
      - заселение товаров на inbound со статусом inbound
    При статусе completed
      - заселение товаров на new со статусом new
    """
    errors = []
    items = []

    for index, row in df.iterrows():
        item_code = row["Партномер"].strip().upper()
        if not item_code:
            errors.append(f"Строка {index + 1}: пустой партномер")

        try:
            int(row["Вес г"].strip())
            int(row["Количество"].strip())
        except ValueError:
            errors.append(f"Строка {index + 1}: неверный вес или количество")

        if errors:
            raise Exception("Валидация формы не пройдена:\n" + "\n".join(errors))

        weight = int(row["Вес г"].strip())
        quantity = int(row["Количество"].strip())
        description = row["Описание"].strip()

        item, created = Item.objects.get_or_create(
            item_code=item_code,
            defaults={"weight": weight, "description": description},
        )

        if wave_status == "in_progress":
            PlaceItem.objects.get_or_create(
                item=item, place=inbound_place, quantity=quantity, status="inbound"
            )
        elif wave_status == "completed":
            PlaceItem.objects.get_or_create(
                item=item, place=new_place, quantity=quantity, status="new"
            )
        items.append((item, quantity))

    return items


def create_items_by_out_form(df, wave_status, outbound_place) -> list[tuple[Item, int]]:
    errors = []
    items = []

    for index, row in df.iterrows():
        item_code = row["Партномер"].strip().upper()
        if not item_code:
            errors.append(f"Строка {index + 1}: пустой партномер")

        try:
            int(row["Количество"].strip())
        except ValueError:
            errors.append(f"Строка {index + 1}: неверное количество")

        if errors:
            raise Exception("Валидация формы не пройдена:\n" + "\n".join(errors))

        quantity = int(row["Количество"].strip())

        try:
            item = Item.objects.get(item_code=item_code)
        except Item.DoesNotExist:
            raise Exception(f"Товар {item_code} не найден")

        # общий остаток по складу кроме адреса OUTBOUND со статусом ok
        available_qty = (
            PlaceItem.objects.filter(item=item, status="ok")
            .exclude(place=outbound_place)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        if available_qty < quantity:
            errors.append(
                f"Недостаточно товара {item_code}: "
                f"нужно {quantity}, доступно {available_qty}"
            )

        if errors:
            raise Exception("Валидация формы не пройдена:\n" + "\n".join(errors))

        if wave_status == "in_progress":
            to_move = quantity

            # списываем с реальных мест
            for pi in (
                PlaceItem.objects.filter(item=item, status="ok")
                .exclude(place=outbound_place)
                .order_by("pk")
            ):
                if to_move <= 0:
                    break

                delta = min(pi.quantity, to_move)
                pi.quantity -= delta
                to_move -= delta

                if pi.quantity == 0:
                    pi.delete()
                else:
                    pi.save()

            # заселяем / увеличиваем OUTBOUND
            outbound_pi, _ = PlaceItem.objects.get_or_create(
                item=item,
                place=outbound_place,
                defaults={"quantity": 0, "status": "outbound"},
            )
            outbound_pi.quantity += quantity
            outbound_pi.status = "outbound"
            outbound_pi.save()

        elif wave_status == "completed":
            to_move = quantity
            # списываем с реальных мест
            for pi in (
                PlaceItem.objects.filter(item=item, status="ok")
                .exclude(place=outbound_place)
                .order_by("pk")
            ):
                if to_move <= 0:
                    break

                delta = min(pi.quantity, to_move)
                pi.quantity -= delta
                to_move -= delta

                if pi.quantity == 0:
                    pi.delete()
                else:
                    pi.save()

        items.append((item, quantity))

    return items


def create_items(*, df, wave, status: str, wave_type: str):
    logger.debug("create_items(): wave = %s, status = %s", wave.pk, status)
    if wave_type == "inbound":
        # поиск необходимых адресов
        try:
            inbound_place = Place.objects.get(title="INBOUND")
            new_place = Place.objects.get(title="NEW")
        except Place.DoesNotExist:
            raise Exception("На складе отсутствует технический адрес INBOUND или NEW")

        # валидация полей формы
        # создание объектов Item
        # При статусе in_progress
        #   - заселение товаров на inbound со статусом inbound
        # При статусе completed
        #   - заселение товаров на new со статусом new
        items = create_items_by_inb_form(df, status, inbound_place, new_place)
        # создание у Inbound объектов InboundItem
        for item, quantity in items:
            InboundItem.objects.get_or_create(
                item=item, inbound=wave, total_quantity=quantity
            )

    elif wave_type == "outbound":
        # поиск необходимого адреса
        try:
            outbound_place = Place.objects.get(title="OUTBOUND")
        except Place.DoesNotExist:
            raise Exception(f"На складе отсутствует технический адрес #OUTBOUND")

        # валидация полей формы
        # При статусе in_progress
        #   - переселение товаров на outbound со статусом outbound
        # При статусе completed
        #   - удаление соответствующего кол-ва товаров с мест
        items = create_items_by_out_form(df, status, outbound_place)
        # создание у Outbound объектов OutboundItem
        for item, quantity in items:
            OutboundItem.objects.get_or_create(
                item=item,
                outbound=wave,
                defaults={"total_quantity": quantity},
            )
