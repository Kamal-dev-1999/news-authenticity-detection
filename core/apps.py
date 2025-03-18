# apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from .model import get_models
        try:
            get_models()
        except RuntimeError as e:
            print(f"Model initialization error: {str(e)}")