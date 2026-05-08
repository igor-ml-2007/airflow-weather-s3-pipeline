from __future__ import annotations

from typing import Any

from airflow.decorators import dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from pendulum import datetime

from weather_pipeline.pipeline import (
    build_object_key,
    build_public_object_url,
    build_report,
    fetch_current_temperatures,
    get_s3_bucket_name,
    serialize_report,
)


@dag(
    dag_id="weather_russia_to_s3",
    schedule="0 */6 * * *",
    start_date=datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["python", "weather", "s3"],
)
def weather_russia_to_s3() -> None:
    @task
    def fetch_weather() -> list[dict[str, Any]]:
        return fetch_current_temperatures()

    @task
    def calculate_average(measurements: list[dict[str, Any]]) -> dict[str, Any]:
        return build_report(measurements)

    @task
    def upload_to_s3(report: dict[str, Any]) -> dict[str, str]:
        bucket_name = get_s3_bucket_name()
        object_key = build_object_key(report)

        S3Hook(aws_conn_id="minio_default").load_string(
            string_data=serialize_report(report),
            key=object_key,
            bucket_name=bucket_name,
            replace=True,
        )

        return {
            "bucket": bucket_name,
            "key": object_key,
            "s3_uri": f"s3://{bucket_name}/{object_key}",
            "public_url": build_public_object_url(bucket_name, object_key),
        }

    upload_to_s3(calculate_average(fetch_weather()))


weather_russia_to_s3()
