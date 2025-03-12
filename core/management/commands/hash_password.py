# core/management/commands/hash_password.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = "Hash a plaintext password using Django's built-in password hasher"

    def add_arguments(self, parser):
        parser.add_argument("password", type=str, help="The plaintext password to hash")

    def handle(self, *args, **options):
        plaintext = options["password"]
        hashed = make_password(plaintext)
        self.stdout.write(hashed)
