# core/management/commands/create_superuser.py
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    _help = "Create a superuser if one does not already exist, "
    help = f"{_help}using env vars for hashed credentials."

    def handle(self, *args, **options):
        User = get_user_model()
        username = settings.SUPERUSER_NAME
        email = settings.SUPERUSER_EMAIL
        password = settings.SUPERUSER_PASS

        if not username or not email or not password:
            msg = "DEPO_SUPERUSER_NAME, DEPO_SUPERUSER_EMAIL, "
            msg += "& DEPO_SUPERUSER_PASS must be set."
            self.stdout.write(self.style.ERROR(msg))
            return

        if User.objects.filter(username=username).exists():
            msg = f'Superuser "{username}" already exists.'
            self.stdout.write(self.style.WARNING(msg))
            return

        # Check if the password looks already hashed. (Default Django hashers include "pbkdf2_sha256$", "argon2$", etc.)
        if (
            password.startswith("pbkdf2_sha256$")
            or password.startswith("argon2$")
            or password.startswith("bcrypt$")
        ):
            # Create the user and assign the pre-hashed password.
            user = User.objects.create(
                username=username,
                email=email,
                is_staff=True,
                is_superuser=True,
            )
            user.password = password  # directly assign the hashed password
            user.save()
            msg = f'Superuser "{username}" created successfully with a pre-hashed password.'
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            # Fallback: Create superuser using plaintext which will be hashed automatically.
            kwargs = {"username": username, "email": email, "password": password}
            User.objects.create_superuser(**kwargs)  # pyright: ignore
            msg = f'Superuser "{username}" created successfully with auto-hashing.'
            self.stdout.write(self.style.SUCCESS(msg))
