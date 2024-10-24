from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("", include("link.urls")), # Doesn't work?
]
