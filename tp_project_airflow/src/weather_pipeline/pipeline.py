from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_S3_BUCKET = "weather-results"
DEFAULT_S3_PREFIX = "weather-averages"
DEFAULT_PUBLIC_ENDPOINT = "http://localhost:9000"


@dataclass(frozen=True, slots=True)
class City:
    name: str
    latitude: float
    longitude: float


RUSSIAN_CITIES: tuple[City, ...] = (
    City("Moscow", 55.7558, 37.6173),
    City("Saint Petersburg", 59.9386, 30.3141),
    City("Kaliningrad", 54.7104, 20.4522),
    City("Murmansk", 68.9707, 33.0749),
    City("Kazan", 55.7961, 49.1064),
    City("Sochi", 43.5855, 39.7231),
    City("Yekaterinburg", 56.8389, 60.6057),
    City("Novosibirsk", 55.0084, 82.9357),
    City("Krasnoyarsk", 56.0153, 92.8932),
    City("Irkutsk", 52.2869, 104.305),
    City("Yakutsk", 62.0281, 129.7326),
    City("Vladivostok", 43.1155, 131.8855),
)


def fetch_current_temperatures(cities: tuple[City, ...] = RUSSIAN_CITIES) -> list[dict[str, Any]]:
    measurements: list[dict[str, Any]] = []

    for city in cities:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": city.latitude,
                "longitude": city.longitude,
                "current": "temperature_2m",
                "timezone": "UTC",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current") or {}
        temperature = current.get("temperature_2m")
        observed_at = current.get("time")

        if temperature is None or observed_at is None:
            raise ValueError(f"Open-Meteo response for {city.name} does not contain current temperature")

        measurements.append(
            {
                "city": city.name,
                "latitude": city.latitude,
                "longitude": city.longitude,
                "temperature_c": float(temperature),
                "observed_at": observed_at,
            }
        )

    return measurements


def build_report(measurements: list[dict[str, Any]]) -> dict[str, Any]:
    if not measurements:
        raise ValueError("At least one city is required to calculate an average temperature")

    temperatures = [float(item["temperature_c"]) for item in measurements]
    generated_at = datetime.now(timezone.utc)

    return {
        "generated_at": generated_at.isoformat(),
        "source": "Open-Meteo",
        "unit": "celsius",
        "city_count": len(measurements),
        "average_temperature_c": round(mean(temperatures), 2),
        "minimum_temperature_c": min(temperatures),
        "maximum_temperature_c": max(temperatures),
        "measurements": measurements,
    }


def get_s3_bucket_name() -> str:
    return os.getenv("WEATHER_S3_BUCKET", DEFAULT_S3_BUCKET)


def get_s3_prefix() -> str:
    return os.getenv("WEATHER_S3_PREFIX", DEFAULT_S3_PREFIX).strip("/")


def build_object_key(report: dict[str, Any]) -> str:
    generated_at = datetime.fromisoformat(str(report["generated_at"]))
    filename = f"weather_average_{generated_at:%Y%m%dT%H%M%SZ}.json"
    prefix = get_s3_prefix()

    if not prefix:
        return filename

    return f"{prefix}/{generated_at:%Y/%m/%d}/{filename}"


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)


def build_public_object_url(bucket_name: str, object_key: str) -> str:
    endpoint = os.getenv("WEATHER_S3_PUBLIC_ENDPOINT", DEFAULT_PUBLIC_ENDPOINT).rstrip("/")
    return f"{endpoint}/{bucket_name}/{object_key}"

