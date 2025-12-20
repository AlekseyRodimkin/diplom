import datetime
import os
import re

from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from django.conf import settings

from .fonts import register_fonts
from .styles import BASE, TITLE_BOLD
from .tables import products_table


def validate_recipient(recipient: str) -> str:
    if not recipient:
        return recipient

    recipient = recipient.strip()
    if not recipient:
        return recipient

    forms = [
        "ООО", "ЗАО", "ОАО", "АО", "ПАО",
        "ИП", "НОУ", "ГОУ", "МУП", "ГУП",
        "ФГУП", "НКО", "ТСЖ", "ЖСК"
    ]

    pattern = r'^(\s*)(' + '|'.join(re.escape(f) for f in forms) + r')(\s+)(.+)$'

    def repl(match):
        leading_spaces = match.group(1)
        form_original = match.group(2)
        spaces_between = match.group(3)
        company_name = match.group(4).strip()

        form_normalized = form_original.upper()

        return f"{leading_spaces}{form_normalized} «{company_name}»"

    result = re.sub(pattern, repl, recipient, flags=re.IGNORECASE)

    return result


def generate_packing_list_pdf(outbound):
    register_fonts()

    # Путь к файлу
    dir_path = outbound.get_uploads_dir()
    filename = os.path.join(dir_path, f"PACK_{outbound.outbound_number}.pdf")

    # Данные таблицы
    data = [["Партномер", "Ед.изм", "Кол-во", "Масса г", "Примечание"]]
    total_weight = 0
    recipient = validate_recipient(outbound.recipient)

    for outbound_item in outbound.outbound_items.select_related("item").all():
        item = outbound_item.item
        weight_gram = getattr(item, "weight", 0) or 0
        row_weight = outbound_item.total_quantity * weight_gram / 1000
        total_weight += row_weight

        data.append([
            item.item_code or "",
            "шт",
            str(outbound_item.total_quantity),
            str(weight_gram),
            item.description_short or "",
        ])

    # Создание документа
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    elements.append(Paragraph("Упаковочный лист", TITLE_BOLD))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        f'<font name="OpenSans-Bold">Отправитель: </font><font name="OpenSans">{getattr(settings, "COMPANY_NAME", "ООО «Компания»")}</font>',
        BASE))
    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(f'<font name="OpenSans-Bold">Заказчик: </font><font name="OpenSans">{recipient}</font>',
                  BASE))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f'<font name="OpenSans-Bold">Масса нетто: </font>{total_weight:.1f} кг', BASE))
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(f'<font name="OpenSans-Bold">Дата: </font>{datetime.date.today().strftime("%d.%m.%Y")}', BASE))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('<font name="OpenSans-Bold">Упаковал: </font>', BASE))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('<font name="OpenSans-Bold">Род упаковки: </font>', BASE))
    elements.append(Spacer(1, 20))

    elements.append(products_table(data))
    elements.append(Spacer(1, 20))

    doc.build(elements)

    return filename
