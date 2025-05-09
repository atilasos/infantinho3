from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals # noqa: F401
        # Ensure other signals or startup code is also imported if present
        # For example, if you have other signal files:
        # import users.other_signals # noqa: F401
