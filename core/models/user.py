# core/models/user.py
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password as chkpass
from django.http import HttpResponse

from functools import wraps
import jwt


# TODO: Add factory class method that also sets password and saves user
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


def unauthorized_response(msg: str) -> HttpResponse:
    return HttpResponse(
        msg, content_type="text/plain", status=401, headers={"X-Error": "true"}
    )


# TODO: Figure out how to differentiate between browser & API requests
#       the browser maybe should be sent to a page showing demanding login
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
            return unauthorized_response("Unauthorized: Bearer JWT token required")
        token = auth_header.split(" ", 1)[1]
        try:  # Decode & verify token
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            request.user_payload = decoded
        except jwt.ExpiredSignatureError:
            return unauthorized_response("Unauthorized: JWT token has expired")
        except jwt.InvalidTokenError:
            return unauthorized_response("Unauthorized: Invalid JWT token")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
