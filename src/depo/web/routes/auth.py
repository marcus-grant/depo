# src/depo/web/routes/auth.py
"""
Authentication routes for depo web layer.
Handles login and logout.
Author: Marcus Grant
Created: 2026-06-23
License: Apache-2.0
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from depo.util.errors import AuthenticationError, NotFoundError
from depo.util.password import verify_password
from depo.web.deps import get_current_uid, get_repo
from depo.web.templates import get_templates

auth_router = APIRouter()


def _render_login(request: Request, error: AuthenticationError | None) -> Response:
    """Render the login page and form with an optional error message."""
    status = error.status if error else 200
    return get_templates().TemplateResponse(
        request=request,
        name="auth/login.html",
        status_code=status,
        context={"error": error},
    )


@auth_router.get("/login")
async def page_login(request: Request) -> Response:
    """Serve the login form as a full HTML page."""
    if get_current_uid(request) is not None:  # Already logged in, redirect home
        return RedirectResponse(url="/", status_code=302)
    return _render_login(request, error=None)  # Render login page


@auth_router.post("/login")
async def handle_login(request: Request) -> Response:
    """Verify credentials and set session cookie on success.
    Or re-render form on login error."""
    # Extract login form data and normalize to strings
    form = await request.form()
    email, password = form.get("email", ""), form.get("password", "")
    email = email if isinstance(email, str) else ""
    password = password if isinstance(password, str) else ""
    auth_err = AuthenticationError(email)  # Hoisted to simplify control flow

    try:  # Try retrieving user by email given
        user = get_repo(request).get_user_by_email(email)
    except NotFoundError:  # If user not found, return login form with error
        return _render_login(request, error=auth_err)
    if not verify_password(password, user.pw_hash):  # Verify password hash matches
        return _render_login(request, error=auth_err)

    # Happy path; credentials match, reset session to user id
    request.session.clear()  # Clear any existing session data
    request.session["uid"] = user.id  # Reset user_id in session
    return RedirectResponse(url="/", status_code=302)


@auth_router.get("/logout")
async def handle_logout(request: Request) -> Response:
    """Clear the session and redirect to root."""
    request.session.clear()  # Clear session data
    return RedirectResponse(url="/", status_code=302)  # Redirect to root
