# app/__init__.py
from fastapi import FastAPI
from .settings import settings
from .server import app

__version__ = settings.API_VERSION

def get_application() -> FastAPI:
    """Get the FastAPI application instance."""
    return app