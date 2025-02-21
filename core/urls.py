from django.urls import path
from . import views as core_views
from core.viewsnew.user import login_view

urlpatterns = [
    path("", core_views.web_index, name="web_index"),
    path("login", login_view, name="login"),
    path("upload/", core_views.upload_view, name="upload"),
    path(
        "<str:shortcode>/details",
        core_views.shortcode_details,
        name="shortcode_details",
    ),
]
