# core/user/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=32)
    pass_hash = models.CharField(max_length=128)

    def set_password(self, pass_plaintext):
        """Hash the given raw password & store result"""
        # self.password = make_password(pass_plaintext)
        pass
