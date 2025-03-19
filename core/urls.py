from django.contrib import admin
from django.urls import path, include

# from core.views.user import login_view, api_login_view  # TODO: Delete once login works
from core.views.upload import web_upload_view
from core.views.upload_api import UploadAPIView
from core.views.index import web_index
from core.views.shortcode import (
    shortcode_details as item_details,
)  # TODO: Rename view function

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("upload/", web_upload_view, name="web_upload"),
    path("api/upload/", UploadAPIView.as_view(), name="api_upload"),
    path("", web_index, name="index"),
    path(
        "<str:shortcode>/details",
        item_details,
        name="item_details",
    ),
    # TODO: Refactor to new upload loc
]
