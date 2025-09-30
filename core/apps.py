# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    # If you have signals, import them inside ready()
    # def ready(self):
    #     from . import signals  # noqa: F401
    #     ...
