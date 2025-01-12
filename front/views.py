import re
from urllib import parse
from django.shortcuts import redirect, render
from django.http import JsonResponse
from accounts.models import Account
from django.views.decorators.csrf import csrf_exempt
import requests


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
    return redirect("front:profile", pk=account.id)


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



def reviews_list(request):
    # API에서 리뷰 데이터를 가져오는 요청 (적절한 API URL로 수정 필요)
    api_url = "http://127.0.0.1:8000/api/reviews/"  # 실제 API 엔드포인트로 수정하세요.
    response = requests.get(api_url)  # requests.get() 사용

    if response.status_code == 200:
        reviews = response.json()  # 성공적으로 데이터를 받아오면 JSON 형태로 파싱
    else:
        reviews = []  # API 호출 실패 시 빈 리스트로 처리

    return render(request, "reviews/reviews_list.html", {"reviews": reviews})

def review_create(request):
    if request.method == "POST":
        # Extracting review data from the POST request
        title = request.POST.get("title")
        content = request.POST.get("content")
        rating = request.POST.get("rating")  # Assuming there's a rating field
        user = request.user  # Get the currently authenticated user

        # Create the review data dictionary
        review_data = {
            "title": title,
            "content": content,
            "rating": rating,
            "user": user.id  # Pass the user ID
        }

        # Send the data to the API to create a review
        api_url = "http://127.0.0.1:8000/api/reviews/"
        response = requests.post(api_url, data=review_data)

        if response.status_code == 201:
            # Redirect to the reviews list page if successful
            return redirect("front:reviewslist")
        else:
            # If error, return a message or handle the error appropriately
            return JsonResponse({"error": "Failed to create review."}, status=400)

    return render(request, "reviews/review_create.html")