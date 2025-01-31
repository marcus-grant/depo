from django.urls import path
from . import views

urlpatterns = [
    path("", views.web_index, name="web_index"),
    path("<str:shortcode>/details", views.shortcode_details, name="shortcode_details"),
    path("upload/", views.upload_view, name="upload"),
]
