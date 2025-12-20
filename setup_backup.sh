#!/bin/bash
set -euo pipefail

set -a
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
set +a

BACKUP_SCRIPTS_DIR="$PROJECT_DIR/warehouse_backup"
echo 'Создание папки /warehouse_backup'
mkdir -p "$BACKUP_SCRIPTS_DIR"

BACKUP_DIR="$BACKUP_SCRIPTS_DIR/backups"
echo 'Создание папки /warehouse_backup/backups'
mkdir -p "$BACKUP_DIR"

echo 'Создание файла backup.sh'
cat > "$BACKUP_SCRIPTS_DIR/backup.sh" <<'EOS'
#!/bin/bash
set -euo pipefail

set -a
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../" && pwd)/.env"
set +a

DATE=$(date +%Y-%m-%d)
SQL_FILE="$PROJECT_DIR/warehouse_backup/backups/backup-$DATE.sql"
CRYPTED_FILE="$PROJECT_DIR/warehouse_backup/backups/backup-$DATE.gpg"

echo 'Дамп базы'
docker exec -t warehouse_postgres_db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$SQL_FILE"

echo 'Шифрование'
# gpg --encrypt --recipient "$PUB_KEY_ID" -o "$CRYPTED_FILE" "$SQL_FILE"
gpg --batch --yes --trust-model always --encrypt --recipient "$PUB_KEY_ID" -o "$CRYPTED_FILE" "$SQL_FILE"

echo 'Удаляем исходный нешифрованный файл'
rm -f "$SQL_FILE"

echo 'Отправка файла'

FILE_PATH="$CRYPTED_FILE"
FILE_NAME=$(basename "$FILE_PATH")
DIR_PATH=$(dirname "$FILE_PATH")
TOKEN="${YANDEX_TOKEN:?YANDEX_TOKEN не задан}"
YANDEX_FOLDER="$YANDEX_APP_NAME"
KEEP=${KEEP_BACKUPS:-5}

send_bot_notif() {
    if [[ -z "${BOT_TOKEN:-}" || -z "${CHAT_ID:-}" ]]; then
        return 1
    fi

    local url="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage"
    local text="Резервная копия '$CRYPTED_FILE' загружена в Яндекс Диск"

    curl -s -X POST "$url" \
         -d "chat_id=${CHAT_ID}" \
         -d "text=${text}" > /dev/null
}

echo 'Запрос ссылки по url: https://cloud-api.yandex.net/v1/disk/resources/upload?path=$YANDEX_FOLDER/$FILE_NAME&overwrite=true'
UPLOAD_URL=$(curl -s -H "Authorization: OAuth $TOKEN" \
  "https://cloud-api.yandex.net/v1/disk/resources/upload?path=/Приложения/$YANDEX_FOLDER/$FILE_NAME&overwrite=true" | \
  jq -r '.href')

if [[ -z "$UPLOAD_URL" || "$UPLOAD_URL" == "null" ]]; then
  echo "Ошибка получения URL для загрузки"
  exit 1
fi

echo "Загружаем $FILE_NAME на Яндекс.Диск..."
curl -s --progress-bar -T "$FILE_PATH" "$UPLOAD_URL" | cat

if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
  send_bot_notif
  echo "Файл успешно загружен"
else
  echo "Ошибка загрузки"
  exit 1
fi

echo "Очистка старых бэкапов (оставляем $KEEP последних)..."
mapfile -t FILES < <(ls -1t "$DIR_PATH"/backup-*.gpg 2>/dev/null || true)

if [[ ${#FILES[@]} -le $KEEP ]]; then
  echo "Нечего удалять"
else
  for ((i=$KEEP; i<${#FILES[@]}; i++)); do
    echo "Удаляем ${FILES[$i]}"
    rm -f "$DIR_PATH/${FILES[$i]}"
  done
fi
EOS

chmod +x "$BACKUP_SCRIPTS_DIR/backup.sh"
echo 'Файл backup.sh теперь исполняемый'

echo 'Производится настройку cron для ежедневного запуска генерации бэкапа, шифрования и отправки на Yandex Disk'
CRON_CMD="0 0 * * * /usr/bin/bash $BACKUP_SCRIPTS_DIR/backup.sh >> "$BACKUP_SCRIPTS_DIR/backup.log" 2>&1"
(crontab -l 2>/dev/null | grep -F -q "$BACKUP_SCRIPTS_DIR/backup.sh") || (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
