# core/views/user.py
from datetime import UTC, datetime, timedelta
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import jwt

from core.models.user import User

# NOTE: To simplify initially, use Django SECRET_KEY as JWT secret with short expiration
# TODO: Come up with a better secret key system for JWT
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 60 * 60  # 1 hour


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
        resp = HttpResponse(msg, content_type="text_plain", status=401)
        resp["X-Error"] = "true"
        return resp

    # Format token
    expires = datetime.now(UTC) + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    token_payload = {"name": user.name, "email": user.email, "exp": expires}
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return HttpResponse(
        token, content_type="text/plain", headers={"X-Auth-Token": token}
    )
