from django.urls import path
from . import views as core_views
from .user import views as user_views

urlpatterns = [
    path("", core_views.web_index, name="web_index"),
    path("login", user_views.login_view, name="login"),
    path(
        "<str:shortcode>/details",
        core_views.shortcode_details,
        name="shortcode_details",
    ),
    path("upload/", core_views.upload_view, name="upload"),
]
