from django.urls import path

from . import views

app_name = "front"
urlpatterns = [
    path("signin", views.signin, name="signin"),
    path("signup", views.signup, name="signup"),
    path("mypage", views.mypage, name="mypage"),
    path("edit_account/", views.edit_account, name="edit_account"),
]
