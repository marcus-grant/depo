# core/views/user.py
from datetime import UTC, datetime, timedelta
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import jwt
from typing import Optional as Opt

from core.models.user import User

# NOTE: To simplify initially, use Django SECRET_KEY as JWT secret with short expiration
# TODO: Come up with a better secret key system for JWT
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 60 * 60  # 1 hour


# TODO: Move to User model class
# TODO: Test in isolation
def validate_user_creds(email: Opt[str], password: Opt[str]) -> Opt[User]:
    """
    Validates user credentials by checking the email and password.
    Args:
        email (str): The email address of the user.
        password (str): The password of the user.
    Returns:
        Optional[User]: The User object if the credentials are valid,
        otherwise None. Returns None if the user does not exist or if
        the password is incorrect.
    Raises:
        User.DoesNotExist: If the user with the given email does not exist.
    Example:
        user = validate_user_creds("user@example.com", "securepassword")
        if user:
            print("Login successful")
        else:
            print("Invalid credentials")
    """
    if email is None or password is None:
        return None  # No email or password provided
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None  # User does not exist
    if user.check_password(password):
        return user  # User exists & password is correct
    return None  # User exists but password is incorrect


# TODO: Move to User model class or util class
# TODO: Test in isolation
def create_jwt(user: User) -> str:
    """Creates a JWT token for a given user.
    Args:
        user (User): Authenticated User object, the token is to be created for.
    Returns:
        str: The JWT token string for the given user.
    Raises:
        JWTError: If there is an error creating the JWT token with provided info.
    """
    token = jwt.encode(
        {
            "name": user.name,
            "email": user.email,
            "exp": datetime.now(UTC) + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


# TODO: Move to a util module
# TODO: Test in isolation
def invalid_method_response(method: str, allowed: str) -> HttpResponse:
    msg = f"Method ({method}) not allowed"
    resp = HttpResponse(msg, content_type="text/plain", status=405)
    resp["X-Error"] = "true"
    resp["Allow"] = allowed
    return resp
# TODO: Figure out how to properly implement CSRF protection
# TODO: User should have a validate func to eval if a given JWT is valid (name,email,exp,signature)
# TODO: Refactor Http responses should have a helper
# TODO: Refactor to pull JWT payload formatting into separate function or even util module
# TODO: Add password validation & potentially UserManager/AbstractUser classes
# Is it needed? Prefer plain text w/ headers
# TODO: Reconsider JWT for HTTPOnly cookies I'm not convinced their extra complexity comes with better security without using a claims system
@csrf_exempt  # For simplicity before real deployment, consider real CSRF handling
def login_view(req):
    method = req.method
    if method == "GET":
        return render(req, "login.html")

    if method != "POST":  # Method not allowed if not GET or POST
        # msg = "Method not allowed"
        # resp = HttpResponse(msg, content_type="text/plain", status=405)
        # resp["X-Error"] = "true"
        # resp["Allow"] = "GET, POST"
        return invalid_method_response(method, "GET, POST")

    # TODO: Implement errors for all NON-POST requests

    email = req.POST.get("email")
    password = req.POST.get("password")  # TODO: Is this really secure?

    # Authenticate user
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None
    if user is None or not user.check_password(password):
        msg = "Access unauthorized due to mismatch between email and password"
        resp = HttpResponse(msg, content_type="text/plain", status=401)
        resp["X-Error"] = "true"
        return resp

    # Format token
    expires = datetime.now(UTC) + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    token_payload = {"name": user.name, "email": user.email, "exp": expires}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # For web logins: set cookie & redirect to index
    resp = HttpResponseRedirect(reverse("index"))

    return HttpResponse(
        token, content_type="text/plain", headers={"X-Auth-Token": token}
    )


@csrf_exempt
def api_login_view(req: HttpRequest) -> HttpResponse:
    # return HttpResponse("TODO: Implement", status=501)
    # if req.method != "POST":
    #     msg = "Method not allowed"
    #     resp = HttpResponse(msg, content_type="text/plain", status=405)
    #     resp["X-Error"] = "true"
    #     resp["Allow"] = "POST"
    #     return resp
    user = validate_user_creds(req.POST.get("email"), req.POST.get("password"))
    # TODO: Implement None return indicating invalid credentials

    token = create_jwt(user)

    resp = HttpResponse(token, status=200, content_type="text/plain")
    resp["X-Auth-Token"] = token
    return resp
