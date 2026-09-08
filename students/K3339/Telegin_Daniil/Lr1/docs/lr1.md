# Лабораторная работа 1: серверное приложение FastAPI

## Тема

Сервис управления личными финансами. Пользователь ведёт счета, категории, финансовые операции, бюджеты и теги.

## Стек

- Python 3.11, FastAPI и Pydantic;
- PostgreSQL 16 в Docker Compose;
- SQLModel / SQLAlchemy;
- Alembic;
- bcrypt;
- собственная реализация JWT HS256 на стандартной библиотеке Python.

## Модель данных

| Таблица | Назначение |
| --- | --- |
| `user` | Пользователь: email, имя, хэш пароля. |
| `account` | Счёт пользователя и текущий баланс. |
| `category` | Категория дохода или расхода. |
| `transaction` | Финансовая операция. |
| `tag` | Тег пользователя. |
| `transactiontaglink` | Связь операции и тега; содержит `applied_at`. |
| `budget` | Лимит категории на период. |

Связи `user → account/category/tag/budget`, `account → transaction` и `category → transaction` — one-to-many. Связь `transaction ↔ tag` — many-to-many через `transactiontaglink`. Поле `applied_at` характеризует саму связь, поэтому ассоциативная сущность соответствует условию работы.

## Подключение к БД

URL хранится в исключённом из Git файле `.env` в переменной `DATABASE_URL`. Шаблон настроек находится в `.env.example`. Контейнер PostgreSQL запускается командой `docker compose up -d db`.

## Миграции

Alembic использует `DATABASE_URL` из `.env`. Выполнены миграции:

1. `create finance schema` — создание семи таблиц и индексов.
2. `default tag assignment timestamp` — серверное значение по умолчанию для `transactiontaglink.applied_at`.

Применение: `alembic upgrade head`. Проверка согласованности моделей и схемы: `alembic check`.

## API

| Группа | Методы |
| --- | --- |
| Аутентификация | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/change-password` |
| Пользователи | `POST /users`, `GET /users` |
| Счета | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` по `/accounts` |
| Категории | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` по `/categories` |
| Теги | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` по `/tags` |
| Бюджеты | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` по `/budgets` |
| Операции | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` по `/transactions` |

Запрос `GET /transactions/{id}` возвращает вложенные объекты счёта, категории и тегов. Интерактивная спецификация доступна в Swagger по адресу `/docs`.

## Авторизация

Пароли не сохраняются в открытом виде: используется bcrypt. JWT создаётся вручную: заголовок и полезная нагрузка кодируются base64url, подпись формируется `HMAC-SHA256` с секретом `JWT_SECRET`. Токен передаётся в заголовке `Authorization: Bearer <token>`.

## История выполнения

| Этап | Коммит |
| --- | --- |
| Базовый FastAPI-проект | `06e421b` |
| Практика 1: временная БД и Pydantic CRUD | `37d2b2c` |
| SQLModel-схема и Compose | `e053af1` |
| Практики 2–3: PostgreSQL, Alembic и CRUD | `dffdbd2` |
| JWT и полный CRUD | `763abe9` |

Перед сдачей репозиторий нужно опубликовать в личном форке, а ссылки на эти коммиты добавить в описание pull request.
