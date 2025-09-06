from django.apps import AppConfig


class MarketplaceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketplace_app'

    def ready(self):
        import marketplace_app.signals
