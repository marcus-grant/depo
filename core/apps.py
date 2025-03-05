import json
import logging
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.hashers import make_password

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    # Add a path attribute pointing to the directory of this file.
    path = str(Path(__file__).resolve().parent)

    def ready(self):
        """When apps are loaded and migrations made, call prepopulation."""
        from django.db.models.signals import post_migrate

        post_migrate.connect(self.prepopulate_users, sender=self)

    def prepopulate_users(self, **kwargs):
        # Import the User model (assuming it is in core/models/user.py)
        from core.models.user import User

        print("Prepopulating users")

        # Get the config file path from settings.
        cfg_file = getattr(settings, "USERS_FILE", None)
        if not cfg_file or not cfg_file.exists():
            return  # Config file setting or file itself doesn't exist
        try:
            with open(cfg_file, "r") as f:
                cfg_users = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error for users file: {e}")
            return
        except FileNotFoundError as e:
            logger.error(f"Error reading users file: {e}")
            return
        for cfg_user in cfg_users:
            # Determine if a user with this email already exists.
            if not User.objects.filter(email=cfg_user["email"]).exists():
                name, email = cfg_user["name"], cfg_user["email"]
                hashed = make_password(cfg_user["password"])
                User.objects.create(email=email, name=name, pass_hash=hashed)
                logger.info(f"User {name} created with email {email}")
                print(f"User {name} created with email {email}")
            else:
                msg = f"User with email {cfg_user['email']} already exists, skipping."
                logger.info(msg)
        logger.info("User prepopulation complete")
        print("User prepopulation complete")
