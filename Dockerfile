FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY tests ./tests
COPY fixtures ./fixtures
RUN mkdir -p /data

EXPOSE 8080

CMD ["uvicorn", "main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]
