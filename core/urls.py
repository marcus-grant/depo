from django.urls import path
from . import views

urlpatterns = [
    path("", views.web_index, name="web_index"),
    path("<str:short_id>/details", views.shortcode_details, name="shortcode_details"),
]
