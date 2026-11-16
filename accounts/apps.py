from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_roles(sender, **kwargs):
    """Make sure the five SchoolAid roles exist after every migrate."""
    from .models import Role

    for name in Role.ALL:
        Role.objects.get_or_create(role_name=name)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(create_default_roles, sender=self)
