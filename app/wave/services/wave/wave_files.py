import io
import logging
import os
import zipfile

import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)

INBOUND_REQUIRED_COLS = {"Партномер", "Вес г", "Количество", "Описание"}
OUTBOUND_REQUIRED_COLS = {"Партномер", "Количество"}


def parse_wave_form_file(file_path: str, wave_type: str):
    """Проверяет наличие необходимых колонок в форме"""
    logger.debug("parse_items_file(): %s", file_path)
    if file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path, dtype=str)
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path, dtype=str)
    else:
        raise Exception("Неподдерживаемый формат файла")

    df = (
        df.astype(str)
        .replace(["nan", "NaN", "None", "<NA>"], "")
        .apply(lambda x: x.str.strip())
    )

    missing = (
        INBOUND_REQUIRED_COLS - set(df.columns)
        if wave_type == "inbound"
        else OUTBOUND_REQUIRED_COLS - set(df.columns)
    )
    if missing:
        raise Exception(f"Отсутствуют колонки: {', '.join(missing)}")

    return df


def build_zip_from_folder(folder_path: str) -> io.BytesIO | None:
    """
    Собирает zip-архив из файлов папки в памяти.
    Возвращает BytesIO с архивом.
    """
    if not os.path.exists(folder_path):
        return None

    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    if not files:
        return None

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in files:
            zip_file.write(os.path.join(folder_path, filename), arcname=filename)

    buffer.seek(0)
    return buffer


def save_file(folder: str, file) -> str | None:
    """Функция сохранения файла"""
    logger.debug("save_file(): %s/%s", folder, file)
    filename = os.path.basename(file.name)
    file_path = os.path.join(folder, filename)
    with open(file_path, "wb+") as dest:
        for chunk in file.chunks():
            dest.write(chunk)
    return file_path


def validate_and_save_wave_files(*, folder, files):
    """Функция проверки размера и расширения файла"""
    for file in files:
        if file.size > settings.MAX_FILE_SIZE:
            raise Exception(f"Файл {file.name} слишком большой")

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.ALLOWED_EXTS_DOCS:
            raise Exception(f"Недопустимое расширение: {file.name}")

        save_file(folder, file)
