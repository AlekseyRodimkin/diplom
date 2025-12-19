#!/bin/bash
set -euo pipefail

set -a
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
set +a

# Ваш полный путь к папке проекта
$BACKUP_SCRIPTS_DIR="$(PROJECT_DIR)/warehouse_backup"
mkdir -p "$BACKUP_SCRIPTS_DIR"

BACKUP_DIR="$BACKUP_SCRIPTS_DIR/backups"
mkdir -p "$BACKUP_DIR"

cat > "$BACKUP_SCRIPTS_DIR/backup_to_storage.py" <<'PYTHON'
import sys
import requests
import os
from pathlib import Path

YANDEX_DISK_BASE_URL = "https://cloud-api.yandex.net/v1/disk"
BACKUP_DIR = Path.home() / "warehouse_backup" / "backups"

files = sorted(BACKUP_DIR.glob("backup-*.gpg"))


def delete_old_backup(keep=5):
    if len(files) <= keep:
        print(f"Бэкапов меньше или равно {keep}, ничего не удаляем.")
    else:
        to_delete = files[:-keep]
        print(f"Удаляем {len(to_delete)} старых файлов:")
        for f in to_delete:
            print(f"Удаляем {f}")
            f.unlink()


def _auth_headers(token: str) -> dict:
    """Формирование заголовков авторизации."""
    return {"Authorization": f"OAuth {token}"}


def upload_file_to_disk(
        dir_path: str,
        file_name: str,
        disk_folder_path: str,
        ya_token: str,
) -> bool:
    """Загрузка файла на Яндекс Диск."""
    print(
        f"upload_file_to_disk(dir_path={dir_path}, file_name={file_name}, "
        f"disk_folder_path={disk_folder_path})"
    )

    upload_url_api = f"{YANDEX_DISK_BASE_URL}/resources/upload"
    headers = _auth_headers(ya_token)
    params = {"path": f"{disk_folder_path}/{file_name}", "overwrite": "true"}

    path = os.path.join(dir_path, file_name)
    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return False

    try:
        print("Запрос URL загрузки с Яндекс Диска")
        resp = requests.get(upload_url_api, headers=headers, params=params)
        resp.raise_for_status()

        upload_url = resp.json().get("href")
        if not upload_url:
            print("Не удалось получить URL-адрес загрузки.")
            return False

        print("Загрузка файла на Яндекс Диск")
        with open(path, "rb") as f:
            upload_resp = requests.put(upload_url, data=f)
            upload_resp.raise_for_status()

        if upload_resp.status_code == 201:
            print("Файл успешно загружен")
            return True

        print("Загрузка файла не удалась")
        return False

    except requests.RequestException as e:
        print(f"Ошибка при загрузке файла на Яндекс Диск: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Используйте: python3 backup_to_storage.py <путь_к_бэкапу>")
        sys.exit(1)

    file_path = sys.argv[1]
    dir_path, file_name = os.path.split(file_path)
    keep_backups = int(os.environ.get("KEEP_BACKUPS", "5"))

    ya_token = os.environ.get("YANDEX_TOKEN")
    if not ya_token:
        raise RuntimeError("YANDEX_TOKEN не определен")

    upload_file_to_disk(
        dir_path=dir_path,
        file_name=file_name,
        disk_folder_path="/backups",
        ya_token=ya_token,
    )
    delete_old_backup(keep=keep_backups)
PYTHON

cat > "$BACKUP_SCRIPTS_DIR/backup.sh" <<'EOS'
#!/bin/bash
set -euo pipefail

set -a
source ../../.env
set +a

DATE=$(date +%Y-%m-%d)
SQL_FILE="$(PROJECT_DIR)/warehouse_backup/backups/backup-$DATE.sql"
CRYPTED_FILE="$(PROJECT_DIR)/warehouse_backup/backups/backup-$DATE.gpg"

# дамп базы
docker exec -t "$(warehouse_postgres_db)" pg_dump -U "$(POSTGRES_USER)" "$(POSTGRES_DB)" > "$SQL_FILE"

# шифрование
gpg --encrypt --recipient "$PUB_KEY_ID" -o "$CRYPTED_FILE" "$SQL_FILE"

# удаляем исходный нешифрованный файл
rm -f "$SQL_FILE"

# отправка на Яндекс Диск
python3 "$(PROJECT_DIR)"/warehouse_backup/backup_to_storage.py "$CRYPTED_FILE"
EOS

chmod +x "$BACKUP_SCRIPTS_DIR/backup.sh"

sudo apt install -y python3-requests

CRON_CMD="0 0 * * * /usr/bin/bash $BACKUP_SCRIPTS_DIR/backup.sh >> "$BACKUP_SCRIPTS_DIR/warehouse_backup/backup.log" 2>&1"
(crontab -l 2>/dev/null | grep -F -q "$BACKUP_SCRIPTS_DIR/backup.sh") || (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
