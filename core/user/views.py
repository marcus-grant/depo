# core/user/views.py
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import jwt

from core.user.models import User

# NOTE: To simplify initially, use Django SECRET_KEY as JWT secret with short expiration
# TODO: Come up with a better secret key system for JWT
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 60 * 60  # 1 hour


# TODO: Refactor to pull JWT payload formatting into separate function or even util module
# TODO: Should we really use 'application/json' for login?
# Is it needed? Prefer plain text w/ headers
# TODO: Reconsider JWT for HTTPOnly cookies I'm not convinced their extra complexity comes with better security without using a claims system
@csrf_exempt  # For simplicity before real deployment, consider real CSRF handling
def login_view(request):
    # TODO: Implement errors for all NON-POST requests
    payload = json.loads(request.body)
    email = payload.get("email")
    password = payload.get("password")  # TODO: Is this really secure?

    # Authenticate user
    user = User.objects.get(email=email)

    # Format token
    token_payload = {
        "name": user.name,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return JsonResponse({"token": token}, status=200)
