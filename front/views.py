import re
from urllib import parse
from django.shortcuts import redirect, render

from accounts.models import Account


def index(request):
    return render(request, "index.html")


def signin(request):
    return render(request, "account/signin.html")


def signup(request):
    return render(request, "account/signup.html")


def edit(request):
    return render(request, "account/edit.html")


def profile(request, pk):
    return render(request, "account/profile.html", context={"id": pk})


def steam(request):
    user_id = request.GET.get("user_id")  # URL에서 user_id를 가져옵니다

    steam_openid_url = "https://steamcommunity.com/openid/login"
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"http://127.0.0.1:8000/view/steam/callback?user_id={user_id}",  # user_id를 포함하여 반환
        "openid.realm": "http://127.0.0.1:8000/",  # not sure what it is
    }
    param_string = parse.urlencode(params)
    auth_url = steam_openid_url + "?" + param_string
    return redirect(auth_url)


def steam_callback(request):
    steam_url = request.GET.get("openid.claimed_id", "")

    # 'openid.claimed_id'가 존재하는 경우, 스팀 ID 추출
    if steam_url:
        steam_id = steam_url.split("/")[-1]  # URL에서 마지막 부분을 스팀 ID로 처리
        print(steam_id)
        user_id = request.GET.get("user_id")
        account = Account.objects.get(user_id=user_id)
        account.steamId = steam_id
        account.save()
    return redirect("front:mypage")


# def get_steam_user_info(steam_id):
#     key = {
#         "key": "YOUR_STEAM_API_KEY",
#         "steamids": steam_id,  # from who you want to get the information. if you are giving a array, you need to change some code here.
#     }
#     url = (
#         "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0001/?%s"
#         % parse.urlencode(key)
#     )
#     rv = ujson.load(request.urlopen(url))
#     return rv["response"]["players"]["player"][0] or {}
