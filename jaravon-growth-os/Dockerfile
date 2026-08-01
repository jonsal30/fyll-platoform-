FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p /app/data

ENV JARAVON_AUTONOMY_LEVEL=A2
ENV JARAVON_ENGINE_ENABLED=true
ENV JARAVON_DB_PATH=/app/data/jaravon.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
