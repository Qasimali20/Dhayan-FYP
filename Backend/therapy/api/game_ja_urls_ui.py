from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("login/", TemplateView.as_view(template_name="game/ja_login.html"), name="ja-ui-login"),
    path("", TemplateView.as_view(template_name="game/ja_game.html"), name="ja-ui-game"),
]
