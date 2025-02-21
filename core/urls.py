from django.urls import path
from core.views.index import web_index
from core.views.shortcode import shortcode_details
from core.views.user import login_view
from core.views.upload import upload_view

urlpatterns = [
    path("", web_index, name="web_index"),
    path("login", login_view, name="login_view"),
    path("upload/", upload_view, name="upload"),
    path(
        "<str:shortcode>/details",
        shortcode_details,
        name="shortcode_details",
    ),
    # TODO: Refactor to new upload loc
]
