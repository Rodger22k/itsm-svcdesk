FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

COPY src ./src
COPY tests ./tests
COPY fixtures ./fixtures

RUN groupadd --system svcdesk \
    && useradd --system --gid svcdesk --home-dir /nonexistent --shell /usr/sbin/nologin svcdesk \
    && mkdir -p /data \
    && chown -R svcdesk:svcdesk /app /data

USER svcdesk

EXPOSE 8080

CMD ["uvicorn", "main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]
