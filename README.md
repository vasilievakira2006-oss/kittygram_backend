# Kittygram — REST API

Бэкенд сервиса Kittygram: каталог котиков и тематические подборки. Построен на Django REST Framework, аутентификация по токену (Djoser), хранение изображений через Pillow, упаковка в Docker.

## Технологии

| Технология | Назначение |
|------------|------------|
| Python 3.11+ | Язык программирования |
| Django 5.2 | Веб-фреймворк |
| Django REST Framework | REST API |
| Djoser | Регистрация и токен-аутентификация |
| SQLite | База данных |
| Pillow | Обработка изображений |
| Docker | Контейнеризация |

## Структура

```
kittygram_backend/
├── cats/                  # приложение
│   ├── models.py          # Cat, Collection
│   ├── serializers.py     # CatSerializer, CollectionSerializer
│   ├── views.py           # CatViewSet, CollectionViewSet
│   ├── permissions.py     # IsOwnerOrAdminOrReadOnly
│   └── migrations/
├── kittygram_backend/     # настройки Django
│   ├── settings.py
│   └── urls.py
├── media/                 # загруженные фотографии котиков
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example           # шаблон переменных окружения
├── schema.yaml            # OpenAPI 3.0 схема
└── kittygram_collection.json   # Postman-коллекция
```

## Локальный запуск

```bash
# 1. Перейти в папку бэкенда
cd kittygram_backend

# 2. Создать виртуальное окружение
python -m venv venv

# 3. Активировать
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Создать .env (скопировать из .env.example и подставить свой SECRET_KEY)
cp .env.example .env

# 6. Применить миграции
python manage.py migrate

# 7. Создать суперпользователя (для админки и операций администратора)
python manage.py createsuperuser

# 8. Запустить сервер разработки
python manage.py runserver
```

API будет доступен на `http://127.0.0.1:8000/`, админка — на `http://127.0.0.1:8000/admin/`.

## Запуск через Docker

```bash
# Сборка образа и запуск контейнера
docker-compose up --build

# Остановка
docker-compose down
```

Контейнер при сборке выполняет миграции и `collectstatic`. По умолчанию слушает порт 8000. Том `./media` и `./staticfiles` пробрасывается в контейнер, чтобы загруженные фотографии и собранная статика сохранялись на хосте.

Переменные окружения берутся из файла `.env` (не коммитится в репозиторий). Шаблон — в `.env.example`.

## Переменные окружения

| Переменная | Назначение | Пример |
|------------|------------|--------|
| `SECRET_KEY` | Секретный ключ Django. В продакшене должен быть уникальным и нерасшариваемым | `django-insecure-...` |
| `DEBUG` | Режим отладки. В dev — `True`, в проде — `False` | `True` |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую | `localhost,127.0.0.1` |

## Эндпоинты

Базовый URL: `http://127.0.0.1:8000`

### Аутентификация (Djoser)

| Метод | URL | Назначение | Тело запроса |
|-------|-----|------------|--------------|
| POST | `/api/users/` | Регистрация нового пользователя | `{"username":"...", "password":"..."}` |
| POST | `/api/token/login/` | Получить токен | `{"username":"...", "password":"..."}` → `{"auth_token":"..."}` |
| POST | `/api/token/logout/` | Отозвать токен | заголовок `Authorization: Token <key>` |
| GET | `/api/users/me/` | Профиль текущего пользователя | заголовок `Authorization: Token <key>` |

### Котики

| Метод | URL | Назначение | Права |
|-------|-----|------------|-------|
| GET | `/api/cats/?page=N` | Список (пагинация по 9) | Любой |
| POST | `/api/cats/` | Создать котика | Авторизованный |
| GET | `/api/cats/{id}/` | Детали | Любой |
| PUT/PATCH | `/api/cats/{id}/` | Обновить | Владелец или администратор |
| DELETE | `/api/cats/{id}/` | Удалить | Владелец или администратор |

Пример тела при создании котика:

```json
{
  "name": "Хлебарсик",
  "color": "#FFE4C4",
  "birth_year": 2022,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZ..."
}
```

`image` — необязательное поле, передаётся как data-URL с base64. Серверная валидация: `birth_year` ≤ текущий год, `color` — допустимый hex, который преобразуется в имя через `webcolors`.

### Подборки

| Метод | URL | Назначение | Права |
|-------|-----|------------|-------|
| GET | `/api/collections/?page=N&category=cute&sort=popular` | Список с фильтрами | Любой |
| POST | `/api/collections/` | Создать подборку | Авторизованный |
| GET | `/api/collections/{id}/` | Детали с вложенными котиками | Любой |
| PUT/PATCH | `/api/collections/{id}/` | Обновить | Владелец или администратор |
| DELETE | `/api/collections/{id}/` | Удалить | Владелец или администратор |
| GET | `/api/collections/popular/` | Топ-5 по лайкам | Любой |
| POST | `/api/collections/{id}/add_cat/` | Добавить котика в подборку | Владелец подборки |
| POST | `/api/collections/{id}/remove_cat/` | Убрать котика из подборки | Владелец подборки |
| POST | `/api/collections/{id}/like/` | Поставить лайк | Авторизованный |
| POST | `/api/collections/{id}/unlike/` | Убрать лайк | Авторизованный |
| GET | `/api/collections/{id}/cats_paginated/` | Котики подборки (постранично) | Любой |

Допустимые категории: `funny`, `cute`, `sleepy`, `active`, `grumpy`, `other`.

## Права доступа

Реализованы через один permission-класс `IsOwnerOrAdminOrReadOnly` ([cats/permissions.py](cats/permissions.py)), применённый и к `CatViewSet`, и к `CollectionViewSet` совместно с `IsAuthenticatedOrReadOnly`:

- Безопасные методы (GET, HEAD, OPTIONS) — доступны всем (в том числе гостям без токена).
- Создание (POST) — требует токен. Владелец проставляется автоматически через `perform_create`.
- Изменение и удаление (PUT, PATCH, DELETE) — только владелец объекта или администратор (`is_staff` / `is_superuser`).

## Валидация

- `birth_year` не может быть больше текущего года (`validate_birth_year` в `CatSerializer`).
- `category` обязана быть из списка `CATEGORY_CHOICES`.
- `color` — валидный hex, преобразуется в имя через `webcolors`.
- При добавлении котика в подборку проверяются: указан ли `cat_id`, существует ли котик, не добавлен ли он уже.

## Тестирование

В корне лежит Postman-коллекция `kittygram_collection.json` с готовыми запросами. Импортируется в Postman через **File → Import**. Покрывает: регистрацию, получение токена, CRUD по котикам и подборкам, фильтрацию, пагинацию, отрицательный кейс.

Перед запуском проверьте, что бэкенд работает на `http://127.0.0.1:8000`.

## API-документация

OpenAPI 3.0 схема в файле `schema.yaml` — её можно открыть в любом просмотрщике:

- Swagger Editor: https://editor.swagger.io/ (File → Import file → выбрать `schema.yaml`)
- Redocly: `npx @redocly/cli preview-docs schema.yaml`
