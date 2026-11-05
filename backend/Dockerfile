# EduFinance backend: Flask API served by gunicorn
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && useradd --create-home appuser
USER appuser

EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]
