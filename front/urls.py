from django.urls import path

from . import views

app_name = "front"
urlpatterns = [
    # account
    path("signin", views.signin, name="signin"),
    path("signup", views.signup, name="signup"),
    path("edit/", views.edit, name="edit"),
    path("profile/<int:pk>/", views.profile, name="profile"),
    path("steam/login/", views.steam, name="steam"),
    path("steam/callback/", views.steam_callback, name="steam_callback"),
    # reviews
    path("reviews/", views.reviews_list, name="reviews_list"),
    path("review_create/", views.review_create, name="review_create"),
    # chatbot
    path("chatbot/", views.chatbot, name="chatbot"),
]
