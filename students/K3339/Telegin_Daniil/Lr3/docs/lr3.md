# Docker, источники данных и очереди

## Цель работы

Упаковать приложение FastAPI, PostgreSQL и сервис парсинга в Docker; вызвать
парсер синхронно по HTTP и асинхронно через очередь Redis и Celery.

## Архитектура

| Сервис | Роль | Внешний порт |
| --- | --- | ---: |
| `api` | FastAPI ЛР1 с маршрутами ЛР3 | 8000 |
| `parser` | отдельный HTTP-сервис загрузки и разбора страниц | 8001 |
| `db` | PostgreSQL с данными ЛР1 и таблицей `parsed_page` | 5433 |
| `redis` | брокер и backend результатов Celery | — |
| `worker` | Celery worker для фоновых запросов к parser | — |

```text
Клиент ──HTTP──> api ──HTTP──> parser ──SQL──> db
                   │
                   └──Celery task──> redis ──> worker ──HTTP──> parser
```

Файлы ЛР1 не изменялись. При сборке контейнера `api` копируются приложение и
миграции ЛР1, а `lr3_api.py` подключает дополнительные маршруты к уже
существующему объекту FastAPI.

## Docker и Docker Compose

В `docker/api.Dockerfile` устанавливаются зависимости ЛР1 и ЛР3, копируются
миграции Alembic, приложение и расширение API. Перед запуском Uvicorn команда
контейнера выполняет `alembic upgrade head`.

`docker/parser.Dockerfile` собирает независимый FastAPI-сервис парсинга.
При старте parser создаёт таблицу `parsed_page`, если она отсутствует.

`compose.yaml` задаёт общую сеть Docker по умолчанию, healthcheck PostgreSQL и
Redis, зависимости запуска и отдельный named volume `lr3_postgres_data`.
Поэтому контейнеры ЛР3 не используют контейнер и том ЛР1.

Запуск:

```powershell
docker compose up -d --build
docker compose ps
```

Остановка без удаления данных:

```powershell
docker compose down
```

## Синхронный вызов парсера

Маршрут `POST /parser/parse` принимает JSON с URL. `api` передаёт его в
`parser` по внутреннему адресу `http://parser:8001/parse`, а parser извлекает
`<title>` и сохраняет результат в PostgreSQL.

Запрос:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/parser/parse `
  -ContentType 'application/json' `
  -Body '{"url":"https://example.com/"}'
```

Ответ:

```json
{
  "url": "https://example.com/",
  "title": "Example Domain",
  "status_code": 200
}
```

Для проверки загрузки расширения предусмотрен `GET /parser/health`.

## Асинхронный вызов через Celery и Redis

`POST /parser/parse/async` ставит задачу `parse_url_task` в Redis и сразу
возвращает HTTP 202 с идентификатором. Worker получает задачу, вызывает parser
и сохраняет результат в Redis backend. При временной ошибке HTTP задача
повторяется до трёх раз с увеличивающейся задержкой.

```powershell
$queued = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/parser/parse/async `
  -ContentType 'application/json' `
  -Body '{"url":"https://example.com/"}'

Invoke-RestMethod "http://127.0.0.1:8000/parser/tasks/$($queued.task_id)"
```

Маршрут `GET /parser/tasks/{task_id}` возвращает статус (`PENDING`, `STARTED`,
`SUCCESS` или `FAILURE`) и JSON-результат после успешного выполнения.

## Проверка

Проведены реальные интеграционные проверки в Docker:

| Сценарий | Результат |
| --- | --- |
| `GET /parser/health` | `{"status":"ok"}` |
| синхронный `POST /parser/parse` для `https://example.com/` | HTTP 200, `Example Domain`, запись в `parsed_page` |
| фоновый `POST /parser/parse/async` | HTTP 202 и `task_id` |
| `GET /parser/tasks/{task_id}` | `SUCCESS`, результат `Example Domain` |

Во всех случаях PostgreSQL получил строку с URL, заголовком, HTTP-статусом и
признаком `lr3-parser-service`.

## Вывод

Docker Compose позволил изолировать и запустить все компоненты одной командой.
Синхронный маршрут удобен, когда клиенту нужен результат немедленно. Очередь
Celery и Redis не блокирует HTTP-запрос при длительном парсинге и позволяет
переносить выполнение на отдельный worker.
