"""
URL configuration for spartamarket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("logout/", views.logout, name="logout"),
    path("mypage/", views.MypageAPIView.as_view(), name="mypage"),
    path("token/", views.token, name="token"),
    path("refresh/", views.refresh, name="refresh"),
    path("interest/", views.interest, name="interest"),
    path("profile/", views.profile, name="profile"),
    path("steam_profile/", views.steam_profile, name="steam_profile"),
    path("steam_login/", views.steam_login, name="steam_login"),
    path("steam_callback/", views.steam_callback, name="steam_callback"),
    path("block/", views.BlockedUserAPIView.as_view(), name="block"),
    path("notice/", views.NoticeAPIView.as_view(), name="notice"),
    path("notice/<int:notice_id>/", views.NoticeDetailAPIView.as_view(), name="notice_detail"),
    path("friend_request/", views.FriendRequestAPIView.as_view(), name="friend_request"),
    path("friend/", views.FriendAPIView.as_view(), name="friend"),
    path("recommended_games/", views.get_recommended_games, name="recommended_games"),
]
