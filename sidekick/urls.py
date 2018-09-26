from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("send_template", views.send_wa_template_message, name="send_template"),
]
