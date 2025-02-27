from django.apps import AppConfig


class SitescrapersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sitescrapers"

    def ready(self):
        # Import the signals module to ensure signal handlers are registered.
        import sitescrapers.signals

        print("Sitescrapers signals have been imported and registered.")
