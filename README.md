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

...

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
