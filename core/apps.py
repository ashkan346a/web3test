from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Register signal handlers (safe import)
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
