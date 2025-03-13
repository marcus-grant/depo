from django.contrib import admin
from django.urls import path, include
from core.views.index import web_index
from core.views.shortcode import shortcode_details

# from core.views.user import login_view, api_login_view  # TODO: Delete once login works
from core.views.upload import web_upload_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # path("login", login_view, name="login"), # TODO: DELETEME
    # path("api/login", api_login_view, name="api_login"), # TODO: DELETEME
    path("upload/", web_upload_view, name="web_upload"),
    path("", web_index, name="index"),
    path(
        "<str:shortcode>/details",
        shortcode_details,
        name="shortcode_details",
    ),
    # TODO: Refactor to new upload loc
]
