import json
import logging
from pathlib import Path

from django.apps import AppConfig
# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    # Add a path attribute pointing to the directory of this file.
    path = str(Path(__file__).resolve().parent)

    def ready(self):
        """When apps are loaded and migrations completed, call prepopulation."""
        # Connect the prepopulation function to post_migrate signal,
        # which ensures that our user creation happens after all migrations.
        # TODO: Make this prepopulate using the management command & SUPERUSER_* vars
        # post_migrate.connect(self.prepopulate_superuser, sender=self)
        pass

    # TODO: Decide if we really want to prepopulate
    # def prepopulate_superuser(self, **kwargs):
    #     """
    #     Prepopulate Django's built-in user model with a superuser that possesses
    #     all major permissions (is_superuser, is_staff). This function checks for an
    #     existing user with a specific username or email and creates one if it doesn't exist.

    #     COMMENT:
    #     The old method prepopulated a custom User model using a configuration file and Django signals.
    #     This approach relied on reading external JSON configuration and creating users with custom fields.
    #     In contrast, this method utilizes Django's built‑in User model (accessed via get_user_model()),
    #     ensuring that the user is created with proper password hashing and permission flags.
    #     The post_migrate signal is still used, which is a standard way to perform such prepopulation,
    #     though some may opt to use a custom management command or data migration for more control.
    #     """
    #     User = get_user_model()
    #     # Define credentials either directly or via settings.
    #     # For demonstration, we use some hardcoded values.
    #     username = getattr(settings, "SUPERUSER_USERNAME", "admin")
    #     email = getattr(settings, "SUPERUSER_EMAIL", "admin@example.com")
    #     password = getattr(settings, "SUPERUSER_PASSWORD", "adminpass")

    #     if not User.objects.filter(username=username).exists():
    #         try:
    #             # Create superuser with all permissions.
    #             User.objects.create_superuser(
    #                 username=username, email=email, password=password
    #             )
    #             logger.info(f"Superuser '{username}' created with email {email}")
    #             print(f"Superuser '{username}' created with email {email}")
    #         except Exception as e:
    #             logger.error(f"Error creating superuser: {e}")
    #             print(f"Error creating superuser: {e}")
    #     else:
    #         logger.info(f"Superuser '{username}' already exists, skipping.")
    #         print(f"Superuser '{username}' already exists, skipping.")
