ARG AIRFLOW_IMAGE=apache/airflow:2.10.5-python3.11
FROM ${AIRFLOW_IMAGE}

ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.11

COPY requirements.txt /tmp/requirements.txt

USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

