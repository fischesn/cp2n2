ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
ARG SOURCE_SHA256
LABEL cp2n2.r4.source-sha256=${SOURCE_SHA256}
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=UTC
WORKDIR /app
COPY requirements.txt /opt/r4-requirements.txt
RUN python -m pip install --no-cache-dir --report /opt/r4-install-report.json -r /opt/r4-requirements.txt
COPY source/ /app/
