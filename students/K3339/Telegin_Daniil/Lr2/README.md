# Лабораторная работа 2: потоки, процессы и асинхронность

В работе сравниваются `threading`, `multiprocessing` и `asyncio` на двух типах
задач: вычислении суммы чисел и загрузке веб-страниц с сохранением заголовков в
PostgreSQL из ЛР1.

## Структура

- `task1_sum/` — три реализации вычисления суммы;
- `task2_parser/` — три реализации параллельного парсинга;
- `results/` — CSV-файлы с замерами времени;
- `docs/` — материалы отчёта для MkDocs.

## Подготовка окружения

Проект использует ту же PostgreSQL-базу, что и ЛР1. Перед запусками парсинга
нужно запустить БД из ЛР1 и указать строку подключения в переменной окружения
`DATABASE_URL`. Если переменная не задана, применяется адрес локальной БД ЛР1.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Команды запуска и результаты будут добавляться по мере реализации задач.

## Запуск

Запускать команды следует из папки `Lr2` после активации окружения.

```powershell
# Задача 1: три отдельных подхода
python -m task1_sum.threading_sum --save
python -m task1_sum.multiprocessing_sum --save
python -m task1_sum.asyncio_sum --save

# Единый замер задачи 1, три повтора
python -m task1_sum.benchmark --repeats 3

# Задача 2: перед этим запустить PostgreSQL из ЛР1
python -m task2_parser.threading_parser
python -m task2_parser.multiprocessing_parser
python -m task2_parser.asyncio_parser

# Единый замер задачи 2, три повтора
python -m task2_parser.benchmark --repeats 3
```

Для быстрого пробного запуска можно ограничить диапазон и список URL:

```powershell
python -m task1_sum.benchmark --limit 100000 --workers 2 --repeats 1
python -m task2_parser.benchmark --url https://example.com --workers 1 --repeats 1
```
