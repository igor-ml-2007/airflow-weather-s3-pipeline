# Airflow Weather to S3

Решение для 3 варианта контрольной на Python:
- забирает текущую температуру по набору городов России из Open-Meteo;
- считает среднюю температуру в Python-коде;
- сохраняет результат в S3-совместимое хранилище;
- запускается как DAG в Apache Airflow через `docker-compose`.

![Структура проекта: какие технологии были использованы ?]


## Что внутри

- `src/weather_pipeline/pipeline.py` — основная Python-логика: запросы в Open-Meteo, расчёт средней температуры, подготовка JSON-отчёта.
- `dags/weather_to_s3_dag.py` — Airflow DAG `weather_russia_to_s3`.
- `docker-compose.yml` — локальный стек из Airflow, Postgres и MinIO.
- `Dockerfile` — кастомный образ Airflow с Python-зависимостями.

## Как это работает

1. Airflow запускает DAG `weather_russia_to_s3`.
2. Задача `fetch_weather` получает температуру по городам России.
3. Задача `calculate_average` считает среднее значение в Python.
4. Задача `upload_to_s3` складывает JSON-файл в бакет `weather-results`.

Пример пути в S3:

```text
weather-averages/2026/05/09/weather_average_20260509T123456Z.json
```

## Быстрый запуск

```bash
docker compose up --build -d
```

После старта будут доступны:
- Airflow UI: `http://localhost:8080`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

Учётные данные:
- Airflow: `airflow / airflow`
- MinIO: `minio / minio123`

## Как запустить DAG вручную

```bash
docker compose exec airflow-scheduler airflow dags trigger weather_russia_to_s3
```

Проверить статус:

```bash
docker compose exec airflow-scheduler airflow dags list-runs -d weather_russia_to_s3
```

## Как проверить файл в S3

Открыть MinIO Console:

```text
http://localhost:9001
```

Либо посмотреть список объектов из контейнера:

```bash
docker compose exec airflow-scheduler airflow tasks states-for-dag-run weather_russia_to_s3 <dag_run_id>
```

После успешного выполнения DAG в XCom последней задачи будет:
- `s3://weather-results/...`
- публичный URL вида `http://localhost:9000/weather-results/...`

## Настройки

Основные настройки лежат в `docker-compose.yml`:
- `WEATHER_S3_BUCKET`
- `WEATHER_S3_PREFIX`
- `WEATHER_S3_PUBLIC_ENDPOINT`
- `AIRFLOW_CONN_MINIO_DEFAULT`

Список городов для расчёта можно изменить в `src/weather_pipeline/pipeline.py` в кортеже `RUSSIAN_CITIES`.

