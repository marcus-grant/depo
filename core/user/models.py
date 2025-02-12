# core/user/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password as chkpass
from django.http import HttpResponse

from functools import wraps
import jwt


# TODO: Add validation function other modules can use to determine if JWT valid (payload, sig, etc.)
# TODO: Use either django's AbstractBaseUser or User models to get builtin permissions and auth
# TODO: Add unique secrets generated for each user that are persisted
# TODO: Add password validation (length, charset, complexity, common word detection)
# TODO: Implement password salting method & storage
class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=32)
    pass_hash = models.CharField(max_length=128)  # TODO: Rename?

    def set_password(self, pass_plaintext: str):
        """Hash the given raw password & store result"""
        self.pass_hash = make_password(pass_plaintext)

    def check_password(self, pass_plaintext: str) -> bool:
        """Check if provided plaintext password matches stored hash"""
        return chkpass(pass_plaintext, self.pass_hash)

    def __str__(self):
        return self.name


# TODO: Make this work with roles related to User
def jwt_required(view_func):
    """
    Decorator to enforce valid JWT tokens are present in Authorization header.
    Must be as 'Bearer token' header values.
    Meant to wrap django view functions where login is required.
    On success, decoded token payload attached to request (request.user_payload).
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the Authorization header from the request.
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return HttpResponse("Unauthorized: JWT 'Bearer' token required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:  # Decode & verify token
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            request.user_payload = decoded
        except jwt.ExpiredSignatureError:
            return HttpResponse("Unauthorized: JWT token has expired", status=401)
        except jwt.InvalidTokenError:
            return HttpResponse("Unauthorized: Invalid JWT token", status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view
