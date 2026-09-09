# Лабораторная работа 3: Docker, источники данных и очереди

ЛР3 объединяет FastAPI-приложение из ЛР1, веб-парсер из ЛР2, PostgreSQL,
Redis и Celery в Docker Compose.

## Планируемые сервисы

- `api` — расширение приложения ЛР1: синхронный вызов парсера и постановка
  фоновых задач;
- `parser` — отдельный HTTP-сервис парсинга;
- `db` — PostgreSQL с данными ЛР1 и результатами ЛР2;
- `redis` — брокер сообщений Celery;
- `worker` — Celery-воркер для фонового парсинга.

## Запуск

Из папки `Lr3`:

```powershell
docker compose up -d --build
docker compose ps
```

Синхронный парсинг через основной API:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/parser/parse `
  -ContentType 'application/json' `
  -Body '{"url":"https://example.com/"}'
```

Фоновый запуск через Redis и Celery:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/parser/parse/async `
  -ContentType 'application/json' `
  -Body '{"url":"https://example.com/"}'

# Подставить task_id из предыдущего ответа
Invoke-RestMethod http://127.0.0.1:8000/parser/tasks/<task_id>
```

Остановить изолированный стек ЛР3, сохранив данные в Docker volume:

```powershell
docker compose down
```

Подробный отчёт находится в `docs/lr3.md`.
