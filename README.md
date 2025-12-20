# Автоматизированная система учета товара

### Docker контейнеры

- Django App
- Postgresql
- NGINX Proxy
- letsencrypt

### Скриншоты
#### Главная гость
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/main.png" style="width:70%;">

#### Главная
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/main-2.png" style="width:90%;">

#### Просмотр структуры
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/structure-search.png" style="width:90%;">

#### Изменение структуры
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/structure-manager.png" style="width:90%;">

#### Создать поставку
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/inbound-create.png" style="width:90%;">

#### Просмотр поставок
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/inbound-search-1.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/inbound-search-2.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/inbound-status.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/inbound-more.png" style="width:70%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/zip.png" style="width:50%;">

#### Создать отгрузку
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/outbound-create.png" style="width:90%;">

#### Просмотр отгрузок
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/outbound-search-1.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/outbound-search-2.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/outbound-more.png" style="width:90%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/outbound-zip.png" style="width:50%;">
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/pack-list.png" style="width:70%;">

#### Поиск товара
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/item-search.png" style="width:90%;">

#### Поиск партии
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/lot-searh.png" style="width:90%;">

#### Перемещение товара
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/item-move.png" style="width:90%;">

#### История перемещений
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/history.png" style="width:90%;">

#### Просмотр персонала
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/staff-search.png" style="width:90%;">

#### Административная панель
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/admin-dash.png" style="width:90%;">

#### Логин
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/login.png" style="width:90%;">

#### Регистрация
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/README-IMAGES/register.png" style="width:90%;">

### Схемы

#### Схема базы данных
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/schemes/db/db_4.0.png" style="width:70%;">

#### Схема доступов
<img src="https://github.com/AlekseyRodimkin/warehouse/blob/main/schemes/permissions/permissions_4.0.png" style="width:100%;">

### Установка и разворачивание проекта

Настройте сервер и git на нем\
Подключите домен у регистратора на ваш IPV4\
Клонируйте репозиторий с проектом на сервер

Создайте **.env** из **.env.template** командой в корне проекта

```bash
cp .env.template .env
```

Переименуйте файл в папке vhost.d на название своего домена\
Выполните команду в корне проекта

```bash
docker compose build && docker compose up -d
```
При запуске устанавливается фикстура с: группами с назначеными правами, администратором, техническими адресами, 1 складом, 2 зонами и 2 местами.

---

### Бэкапы базы данных

Дампы будут создаваться ежедневно в **00.00**, шифроваться **gpg** ключом и выгружаться на **Яндекс диск**\
После загрузки отправляется уведомление в Телеграм бота об успешной загрузке

- Создайте приложение по ссылке https://oauth.yandex.ru/ с названием "Склад" (при другом исправить в **.env**
  YANDEX_APP_NAME)\
  Выберите доступ: cloud_api:disk.app_folder (Доступ к папке приложения на диске)\
  Перейдите по https://oauth.yandex.ru/authorize?response_type=token&client_id=ваш_ClientID
  вставил в конце ClientID со страницы приложения,
  авторизуйтесь и внесите полученый токен в **.env** файл (YANDEX_TOKEN)

- Создайте телеграм бота в **@BotFather**, получите у него токен бота и вставте в **.env** (BOT_TOKEN)
- Отправьте боту любое сообщение и перейдите по ссылке https://api.telegram.org/bot<ТОКЕН_БОТА>/getUpdates
- Найдите там chat_id и вставьте в **.env** (CHAT_ID)

- Все поля отвечающие за бэкапы

```dotenv
CONTAINER_NAME=warehouse_postgres_db
PROJECT_DIR=полный путь до корневой папки проекта
PUB_KEY_ID=ваш email
YANDEX_TOKEN=ваш токен
YANDEX_APP_NAME=Склад
BOT_TOKEN=ваш токен
CHAT_ID=chat id
```

- Запустите файл по настройке бэкапов

```bash
chmod +x ./setup_backup.sh
./setup_backup.sh
```

Файл создаст папку **/warehouse_backup/backups** в корне проекта, создаст **backup.sh** файл который будет: выгружать
данные, шифровать, удалять незашифрованный файл, отправлять файл на Yandex Диск, уведомлять в Телеграм и удалять все
бэкапы кроме 5 последних. Также добавит настройку cron для ежедневного запуска задачи в 00.00

- Сгенерируйте gpg ключи на локальной машине командой

```bash
gpg --full-generate-key
```

(1) RSA and RSA (default)\
4096\
0\
Имя фамилия\
Почта

- Экспортируйте публичный ключ в файл командой

```bash
gpg --export -a "ваш_@email.com" > public-key.gpg
```

- Отправьте публичный ключ на сервер командой

```bash
scp ~/public-key.gpg <user>@<IPV4>:<полный путь до корневой папки проекта>/warehouse/warehouse_backup
```
- Импортируйте ключ на сервере
```bash
gpg --import public-key.gpg
```

- Расшифровать дамп возможно командой
```bash
gpg -d <backup.gpg> > backup.sql
```

### Полная структура проекта
warehouse\
|____schemes\
| |____logic\
| | |____outbound_way.png\
| | |____inbound_way.excalidraw\
| | |____outbound_way.excalidraw\
| | |____inbound_way.png\
| |____permissions\
| | |____permissions_4.0.excalidraw\
| | |____permissions_4.0.png\
| |____db\
| | |____db_4.0.png\
| | |____db_backup.excalidraw\
| | |____db_backup.png\
| | |____db_4.0.excalidraw\
|____app\
| |____app\
| | |____asgi.py\
| | |______init__.py\
| | |____settings.py\
| | |____urls.py\
| | |____wsgi.py\
| |______init__.py\
| |____uploads\
| | |____inbounds\
| | |____outbounds\
| |____logs\
| | |____app.log\
| |____accounts\
| | |____signals.py\
| | |____migrations\
| | | |______init__.py\
| | | |____0001_initial.py\
| | |____models.py\
| | |____management\
| | | |______init__.py\
| | | |____commands\
| | | | |____createsu.py\
| | | | |______init__.py\
| | |______init__.py\
| | |____apps.py\
| | |____admin.py\
| | |____templates\
| | | |____accounts\
| | | | |____me.html\
| | |____tests.py\
| | |____urls.py\
| | |____views.py\
| |____static\
| |____templates\
| | |____base.html\
| | |____account\
| | | |____password_reset_from_key.html\
| | | |____password_reset_done.html\
| | | |____password_reset_from_key_done.html\
| | | |____email_confirm.html\
| | | |____password_reset.html\
| | | |____login.html\
| | | |____verification_sent.html\
| | | |____password_change.html\
| | | |____signup.html\
| |____manage.py\
| |____staff\
| | |____migrations\
| | | |______init__.py\
| | |____models.py\
| | |______init__.py\
| | |____apps.py\
| | |____forms.py\
| | |____admin.py\
| | |____templates\
| | | |____staff\
| | | | |____staff_header.html\
| | | | |____staff-search.html\
| | |____tests.py\
| | |____urls.py\
| | |____views.py\
| |____wave\
| | |____signals.py\
| | |____migrations\
| | | |______init__.py\
| | | |____0001_initial.py\
| | |____pdf_generator\
| | | |______init__.py\
| | | |____OpenSans-Bold.ttf\
| | | |____styles.py\
| | | |____tables.py\
| | | |____packing_list.py\
| | | |____OpenSans-Regular.ttf\
| | | |____fonts.py\
| | |____models.py\
| | |______init__.py\
| | |____apps.py\
| | |____forms.py\
| | |____admin.py\
| | |____templates\
| | | |____wave\
| | | | |____inbound_header.html\
| | | | |____create-outbound.html\
| | | | |____create-inbound.html\
| | | | |____outbound_header.html\
| | | | |____outbound-search.html\
| | | | |____inbound-search.html\
| | |____tests.py\
| | |____urls.py\
| | |____services\
| | | |______init__.py\
| | | |____wave\
| | | | |______init__.py\
| | | | |____wave_files.py\
| | | | |____wave_items.py\
| | | | |____wave_factory.py\
| | |____views.py\
| |____static_debug\
| | |____favicon.ico\
| | |____forms\
| | | |____INB-FORM.xlsx\
| | | |____OUT-FORM.xlsx\
| | |____css\
| | | |____style.css\
| | |____js\
| | | |____notification.js\
| | | |____scheme_button.js\
| | | |____wave_files.js\
| | | |____set_outbound_status.js\
| | | |____outbound_items_modal.js\
| | | |____out_form_validation.js\
| | | |____set_inbound_status.js\
| | | |____inbound_items_modal.js\
| | | |____inb_form_validation.js\
| | |____assets\
| | | |____man.png\
| | | |____woman.png\
| |____warehouse\
| | |____signals.py\
| | |____migrations\
| | | |______init__.py\
| | | |____0001_initial.py\
| | |____models.py\
| | |______init__.py\
| | |____apps.py\
| | |____forms.py\
| | |____admin.py\
| | |____utils.py\
| | |____templates\
| | | |____warehouse\
| | | | |____item-inventory-search.html\
| | | | |____base.html\
| | | | |____history-inventory-search.html\
| | | | |____lot-inventory-search.html\
| | | | |____move-inventory.html\
| | | | |____main.html\
| | | | |____inventory_header.html\
| | |____fixtures\
| | | |____initial_data.json\
| | |____tests.py\
| | |____urls.py\
| | |____views.py\
| |____structure\
| | |____migrations\
| | | |______init__.py\
| | |____models.py\
| | |______init__.py\
| | |____apps.py\
| | |____forms.py\
| | |____admin.py\
| | |____templates\
| | | |____structure\
| | | | |____structure-manager.html\
| | | | |____structure-search.html\
| | | | |____structure_header.html\
| | |____tests.py\
| | |____urls.py\
| | |____views.py\
|____Dockerfile\
|____Makefile\
|____pyproject.toml\
|____setup_backup.sh\
|____README.md\
|____.env.template\
|____.dockerignore\
|____.gitignore\
|____.env\
|____README-IMAGES\
| |____outbound-more.png\
| |____inbound-more.png\
| |____login.png\
| |____.DS_Store\
| |____item-search.png\
| |____outbound-search-1.png\
| |____structure-manager.png\
| |____main.png\
| |____outbound-search-2.png\
| |____inbound-status.png\
| |____zip.png\
| |____register.png\
| |____outbound-create.png\
| |____item-move.png\
| |____main-2.png\
| |____structure-search.png\
| |____history.png\
| |____pack-list.png\
| |____lot-searh.png\
| |____profile.png\
| |____outbound-zip.png\
| |____inbound-create.png\
| |____inbound-search-2.png\
| |____admin-dash.png\
| |____inbound-search-1.png\
| |____staff-search.png\
|____docker-compose.yml\
|____vhost.d\
| |____im_your_domain\
