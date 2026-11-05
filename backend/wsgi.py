"""WSGI entry point (gunicorn wsgi:app) and FLASK_APP target."""

from app import create_app

app = create_app()
