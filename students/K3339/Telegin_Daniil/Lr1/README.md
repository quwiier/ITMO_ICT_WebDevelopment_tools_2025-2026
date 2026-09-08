# Personal Finance Service

Учебное FastAPI-приложение для учёта личных доходов, расходов, счетов, категорий, бюджетов и тегов.

## Возможности

- PostgreSQL 16 в Docker Compose;
- модели SQLModel и миграции Alembic;
- CRUD для операций, счетов, категорий, тегов и бюджетов;
- вложенный ответ операции: счёт, категория и список тегов;
- регистрация, bcrypt-хэширование паролей и собственная реализация JWT HS256.

## Запуск

1. Создать локальный файл настроек: `Copy-Item .env.example .env`.
2. Запустить БД: `docker compose up -d db`.
3. Создать виртуальное окружение: `python -m venv .venv`.
4. Активировать его: `.venv\Scripts\Activate.ps1`.
5. Установить зависимости: `pip install -r requirements.txt`.
6. Применить миграции: `alembic upgrade head`.
7. Запустить сервер: `uvicorn app.main:app --reload`.

Swagger-документация доступна по адресу `http://127.0.0.1:8000/docs`.

## Основные команды

- `docker compose ps` — проверить PostgreSQL;
- `alembic revision --autogenerate -m "описание изменения"` — создать миграцию;
- `alembic upgrade head` — применить миграции;
- `alembic check` — убедиться, что модели и схема синхронизированы;
- `mkdocs serve` — открыть локальную версию отчёта.

Подробный отчёт находится в `docs/lr1.md`.
