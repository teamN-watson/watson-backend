import re
from urllib import parse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import redirect, render
from accounts.models import Account
import requests
from .forms import ReviewForm


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
    return render(request, "reviews/review_create.html")
    if request.method == "GET":
        app_id = request.GET.get("app_id")  # URL 파라미터에서 app_id 받기
        form = ReviewForm(initial={"app_id": app_id})  # 폼에 초기값 설정
    elif request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user  # 현재 로그인한 사용자 설정
            review.save()
            return redirect("front:reviews_list")  # 성공 후 목록 페이지로 리다이렉트
        else:
            # 폼이 유효하지 않으면 에러 메시지와 함께 다시 렌더링
            return render(request, "reviews/review_form.html", {"form": form})
