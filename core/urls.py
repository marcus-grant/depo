from django.urls import path
from . import views

urlpatterns = [
    path("", views.web_index, name="web_index"),
    # path("create", views.create_item, name="create_item"),
    # path("create", views.create_item, name="create_item"),
    # path("<str:shortcode>", views.item_detail, name="item_detail"),
]
