# core/user/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as chkpass


# TODO: Use either django's AbstractBaseUser or User models to get builtin permissions and auth
# TODO: Add password validation (length, charset, complexity, common word detection)
# TODO: Implement password salting method & storage
class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=32)
    pass_hash = models.CharField(max_length=128)

    def set_password(self, pass_plaintext: str):
        """Hash the given raw password & store result"""
        self.pass_hash = make_password(pass_plaintext)

    def check_password(self, pass_plaintext: str) -> bool:
        """Check if provided plaintext password matches stored hash"""
        return chkpass(pass_plaintext, self.pass_hash)

    def __str__(self):
        return self.name
