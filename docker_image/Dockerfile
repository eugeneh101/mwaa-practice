FROM apache/airflow:2.5.1-python3.10

ENV AIRFLOW_HOME=/usr/local/airflow

USER root

RUN apt-get update && apt-get install -y python3-pip \
    libcurl4-gnutls-dev \
    librtmp-dev \
    python3-dev \
    libpq-dev

USER airflow

WORKDIR ${AIRFLOW_HOME}
# COPY requirements.txt /tmp/requirements.txt
# RUN python3 -m pip install -r /tmp/requirements.txt --use-deprecated legacy-resolver