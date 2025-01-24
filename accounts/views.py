from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView

from .models import (
    Account,
    AccountInterest,
    Interest,
    Block,
    Notice,
    FriendRequest,
    Friend,
    Game,
)

from .serializers import (
    AccountDeleteSerializer,
    AccountSerializer,
    AccountUpdateSerializer,
    InterestSerializer,
    LoginSerializer,
    SignupStep1Serializer,
    SignupStep2Serializer,
    NoticeSerializer,
)

from .steam_service import sync_new_steam_user_data
from reviews.serializers import ReviewSerializer
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import AuthenticationFailed
from django.core.serializers import serialize
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
import environ
import requests
from urllib import parse
import json
from django.contrib.auth import login
import environ
from accounts import serializers
import time


@api_view(["POST"])
def signup(request):
    step = request.data["step"]
    if step == "1":
        serializer = SignupStep1Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response({"message": "정상적인 요청입니다."}, status=200)
    elif step == "2":
        serializer = SignupStep2Serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response({"message": "정상적인 요청입니다."}, status=200)
    elif step == "3":
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            select_ids = request.data.get("select_id").split(",")
            print(select_ids)
            if len(select_ids) == 0:
                return Response({"message": "잘못된 요청2입니다."}, status=400)

            serializer.save()
            # 인증 성공: Token 발급 (or JWT 발급)

            user = authenticate(
                request,
                user_id=request.data["user_id"],
                password=request.data["password"],
            )

            steam_id = request.data.get("steamId")
            if steam_id:
                # DB에 리뷰공개 여부/플레이타임/리뷰 데이터 동기화 다음에 하기 할 때 제외하는 로직
                sync_new_steam_user_data(user)

            refresh = RefreshToken.for_user(user)
            for select_id in select_ids:
                interest = Interest.objects.get(
                    id=int(select_id) + 1
                )  # 관심사 객체 가져오기
                AccountInterest.objects.create(account=user, interest=interest)

            # 응답 반환
            return Response(
                {
                    "message": "회원가입 되었습니다.",
                    "refresh_token": str(refresh),
                    "access_token": str(refresh.access_token),
                    "user": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"message": "잘못된 입력값입니다."}, status=400)
    else:
        return Response({"message": "잘못된 요청3입니다."}, status=400)


@api_view(["POST"])
def signin(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        # 입력 데이터에서 사용자 인증
        user_id = serializer.validated_data["user_id"]
        password = serializer.validated_data["password"]

        try:
            Account.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            return Response({"message": "계정을 찾을 수 없습니다."}, status=400)

        user = authenticate(request, user_id=user_id, password=password)

        if not user:
            return Response({"message": "잘못된 로그인 정보입니다."}, status=400)
        # 인증 성공: Token 발급 (or JWT 발급)
        refresh = RefreshToken.for_user(user)

        # 응답 반환
        return Response(
            {
                "message": "Login successful.",
                "refresh_token": str(refresh),
                "access_token": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "age": user.age,
                    "photo": user.photo.url if user.photo else "",
                    "steamId": user.steamId,
                },
                # "token": token.key,
            },
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        # 현재 사용자의 refresh token을 블랙리스트에 추가
        refresh_token = RefreshToken(request.data["refresh_token"])
        refresh_token.blacklist()

        return Response({"message": "Successfully logged out."}, status=200)
    except TokenError:
        return Response({"message": "Invalid refresh token."}, status=400)


@api_view(["GET"])
def profile(request):
    id = request.GET.get("id")
    user = Account.objects.get(id=id)
    login_user = request.user
    print(login_user, user)
    if user:
        reviews = user.reviews.all()
        data = {
            "reviews_data": ReviewSerializer(reviews, many=True).data,
            "profile_data": AccountSerializer(user).data,
            "friends": {},
            "is_mypage": (
                True
                if login_user.is_anonymous == False and login_user.id == user.id
                else False
            ),
        }

        if user.steamId != None and user.steamId != "":
            api_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"

            try:
                env = environ.Env()
                api_key = env("STEAM_API_KEY")
                # 기본 파라미터 (영문 결과)
                params = {
                    "key": api_key,
                    "steamid": user.steamId,
                    "include_appinfo": True,
                }

                # 한글 결과를 위한 파라미터 추가
                response = requests.get(api_url, params=params)

                # 요청 성공 여부 확인
                if response.status_code == 200:
                    response_data = response.json()["response"]
                    owned_games = sorted(
                        response_data["games"],
                        key=(lambda x: x["playtime_forever"]),
                        reverse=True,
                    )

                    data["owned_games"] = {
                        "games": owned_games[:5],
                        "game_count": response_data["game_count"],
                    }

            except requests.exceptions.RequestException as e:
                return Response({"message": "Invalid request."}, status=400)

            api_url = (
                "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
            )

            try:
                params = {"key": api_key, "steamid": user.steamId, "count": 3}

                # 한글 결과를 위한 파라미터 추가
                response = requests.get(api_url, params=params)

                # 요청 성공 여부 확인
                if response.status_code == 200:
                    response_data = response.json()["response"]
                    data["recent_games"] = response_data

            except requests.exceptions.RequestException as e:
                return Response({"message": "Invalid request."}, status=400)

        return JsonResponse(
            {
                "message": f"{id}번 유저의 프로필 정보",
                "data": data,
            }
        )
    else:
        return Response({"message": "Invalid request."}, status=400)

@api_view(['GET'])
def get_recommended_games(request):
    print("\n=== 추천 게임 API 호출 시작 ===")
    user = request.user
    user_age = user.age
    print(f"요청 유저: {user.nickname} (ID: {user.id})")
    
    # 기본 태그와 플레이한 게임 태그 분리
    user_tags = set(tag.lower() for tag in user.get_steam_tag_names_en())
    all_played_game_tags = set(tag.lower() for tag in user.get_top_played_games_tags())
    
    # played_game_tags를 user_tags와 같은 크기로 제한
    played_game_tags = set(list(all_played_game_tags)[:len(user_tags)])
    
    print("\n=== 유저 태그 정보 ===")
    print(f"기본 태그 ({len(user_tags)}개):", user_tags)
    print(f"플레이한 게임 태그 ({len(played_game_tags)}개):", played_game_tags)
    print(f"유저 나이: {user_age}")

    # 사용자가 보유한 게임의 appID 목록 가져오기
    owned_game_ids = set()
    if user.steamId:
        print(f"\n=== 스팀 연동 정보 ===")
        print(f"스팀 ID: {user.steamId}")
        try:
            env = environ.Env()
            api_key = env("STEAM_API_KEY")
            api_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
            params = {
                "key": api_key,
                "steamid": user.steamId,
                "include_appinfo": True,
            }
            response = requests.get(api_url, params=params)
            
            if response.status_code == 200:
                owned_games = response.json()["response"].get("games", [])
                owned_game_ids = {game["appid"] for game in owned_games}
                print(f"=== 보유한 게임 목록 ===")
                print(f"총 {len(owned_game_ids)}개의 게임 보유")
                print(f"게임 ID 목록: {owned_game_ids}")
        except Exception as e:
            print(f"스팀 게임 목록 조회 실패: {str(e)}")

    # 기본 게임 필터링 (나이 제한, metacritic 점수 있음, 보유하지 않은 게임)
    base_games = Game.objects.filter(
        required_age__lte=user_age,
        metacritic_score__isnull=False
    ).exclude(
        appID__in=owned_game_ids
    ).values(
        'id', 'appID', 'name', 'header_image', 'price', 
        'required_age', 'metacritic_score', 'genres', 'genres_kr',
        'tags', 'categories', 'median_playtime_forever', 'estimated_owners'
    )

    # owners_ranges 정의
    owners_ranges = {
        "0 - 20000": 10,
        "20000 - 50000": 20,
        "50000 - 100000": 30,
        "100000 - 200000": 40,
        "200000 - 500000": 50,
        "500000 - 1000000": 60,
        "1000000 - 2000000": 70,
        "2000000 - 5000000": 80,
        "5000000 - 10000000": 90,
        "10000000 - 20000000": 100,
        "20000000 - 50000000": 110,
        "50000000 - 100000000": 120,
        "100000000 - 200000000": 130,
    }

    # 1. 기본 태그 기반 추천
    print("\n=== 기본 태그 기반 게임 점수 계산 시작 ===")
    interest_based_games = []
    for game in base_games:
        game_tags = json.loads(game['tags']) if isinstance(game['tags'], str) else game['tags']
        game_genres = json.loads(game['genres']) if isinstance(game['genres'], str) else game['genres']
        game_categories = json.loads(game['categories']) if isinstance(game['categories'], str) else game['categories']
        
        game_tags_lower = {tag.lower() for tag in game_tags}
        game_genres_lower = {genre.lower() for genre in game_genres}
        game_categories_lower = {category.lower() for category in game_categories}

        # 매칭된 태그 수 계산
        tags_matched = len(user_tags & game_tags_lower)
        genres_matched = len(user_tags & game_genres_lower)
        categories_matched = len(user_tags & game_categories_lower)

        # 점수 계산
        tag_score = tags_matched * 50
        genre_score = genres_matched * 50
        category_score = categories_matched * 30
        playtime_score = int(min(game['median_playtime_forever'] / 10, 100))
        owners_score = owners_ranges.get(game['estimated_owners'], 0)
        metacritic_score = game['metacritic_score']

        total_score = (
            tag_score + genre_score + category_score + 
            playtime_score + owners_score + metacritic_score
        )

        if total_score > 200:
            print(f"\n게임 '{game['name']}' 점수 상세 (기본 태그):")
            print(f"- 태그 매칭 ({tags_matched}개): {tag_score}")
            print(f"- 장르 매칭 ({genres_matched}개): {genre_score}")
            print(f"- 카테고리 매칭 ({categories_matched}개): {category_score}")
            print(f"- 플레이타임 점수: {playtime_score}")
            print(f"- 소유자 수 점수: {owners_score}")
            print(f"- 메타크리틱 점수: {metacritic_score}")
            print(f"- 총점: {total_score}")

        interest_based_games.append({
            'id': game['id'],
            'appID': game['appID'],
            'name': game['name'],
            'header_image': game['header_image'],
            'price': game['price'],
            'required_age': game['required_age'],
            'metacritic_score': game['metacritic_score'],
            'genres': game_genres,
            'genres_kr': game['genres_kr'],
            'score': total_score
        })

    # 2. 플레이한 게임 태그 기반 추천
    print("\n=== 플레이한 게임 태그 기반 게임 점수 계산 시작 ===")
    playtime_based_games = []
    for game in base_games:
        game_tags = json.loads(game['tags']) if isinstance(game['tags'], str) else game['tags']
        game_genres = json.loads(game['genres']) if isinstance(game['genres'], str) else game['genres']
        game_categories = json.loads(game['categories']) if isinstance(game['categories'], str) else game['categories']
        
        game_tags_lower = {tag.lower() for tag in game_tags}
        game_genres_lower = {genre.lower() for genre in game_genres}
        game_categories_lower = {category.lower() for category in game_categories}

        # 매칭된 태그 수 계산
        tags_matched = len(played_game_tags & game_tags_lower)
        genres_matched = len(played_game_tags & game_genres_lower)
        categories_matched = len(played_game_tags & game_categories_lower)

        # 점수 계산 로직 수정 (전체적인 점수 스케일 조정)
        # 1. 태그/장르/카테고리 매칭 점수
        tag_score = tags_matched * 20  # 30 -> 20
        genre_score = genres_matched * 20  # 30 -> 20
        category_score = categories_matched * 15  # 20 -> 15

        # 2. 게임 인기도/품질 점수
        # 메타크리틱 점수 (원래 점수 그대로 사용)
        metacritic_score = game['metacritic_score']

        # 소유자 수 점수 (가중치 조정)
        owners_score = owners_ranges.get(game['estimated_owners'], 0)

        # 적정 플레이타임 보너스 (점수 범위 축소)
        median_playtime = game['median_playtime_forever']
        if 120 <= median_playtime <= 3000:  # 2시간 ~ 50시간 사이의 게임
            playtime_score = 50  # 100 -> 50
        elif 60 <= median_playtime < 120:  # 1~2시간 게임
            playtime_score = 25  # 50 -> 25
        elif 3000 < median_playtime <= 6000:  # 50~100시간 게임
            playtime_score = 35  # 75 -> 35
        else:
            playtime_score = 10  # 25 -> 10

        total_score = (
            tag_score + genre_score + category_score + 
            playtime_score + owners_score + metacritic_score
        )

        # 메타크리틱 점수가 75점 이상이거나 소유자가 많은 게임만 후보로 선정
        if (game['metacritic_score'] >= 75 or 
            game['estimated_owners'] in [
                "1000000 - 2000000",
                "2000000 - 5000000",
                "5000000 - 10000000",
                "10000000 - 20000000",
                "20000000 - 50000000",
                "50000000 - 100000000",
                "100000000 - 200000000"
            ]):
            if total_score > 200:
                print(f"\n게임 '{game['name']}' 점수 상세 (플레이타임 기반):")
                print(f"- 태그 매칭 ({tags_matched}개): {tag_score}")
                print(f"- 장르 매칭 ({genres_matched}개): {genre_score}")
                print(f"- 카테고리 매칭 ({categories_matched}개): {category_score}")
                print(f"- 플레이타임 점수: {playtime_score}")
                print(f"- 소유자 수 점수: {owners_score}")
                print(f"- 메타크리틱 점수: {metacritic_score}")
                print(f"- 총점: {total_score}")

            playtime_based_games.append({
                'id': game['id'],
                'appID': game['appID'],
                'name': game['name'],
                'header_image': game['header_image'],
                'price': game['price'],
                'required_age': game['required_age'],
                'metacritic_score': game['metacritic_score'],
                'genres': game_genres,
                'genres_kr': game['genres_kr'],
                'score': total_score
            })
    
    # 각각 상위 15개 선택
    import heapq
    recommended_interest_games = heapq.nlargest(15, interest_based_games, key=lambda x: x['score'])
    recommended_playtime_games = heapq.nlargest(15, playtime_based_games, key=lambda x: x['score'])
    
    print("\n=== 최종 추천 게임 목록 ===")
    print("기본 태그 기반 추천:")
    for idx, game in enumerate(recommended_interest_games, 1):
        print(f"{idx}. {game['name']} (점수: {game['score']})")
    print("\n플레이타임 기반 추천:")
    for idx, game in enumerate(recommended_playtime_games, 1):
        print(f"{idx}. {game['name']} (점수: {game['score']})")
    
    return Response({
        'message': '추천 게임 목록입니다.',
        'interest_based_games': recommended_interest_games,
        'playtime_based_games': recommended_playtime_games,
        'interest_tags': list(user_tags),  # 기본 태그 리스트
        'playtime_tags': list(played_game_tags)  # 플레이타임 기반 태그 리스트
    }, status=status.HTTP_200_OK)


class MypageAPIView(APIView):

    @permission_classes([IsAuthenticated])
    def get(self, request):
        user = request.user
        if user.is_anonymous == False:
            return JsonResponse(
                {
                    "message": "회원 수정 정보입니다.",
                    "data": {
                        "user": {
                            "id": user.id,
                            "age": user.age,
                            "email": user.email,
                            "nickname": user.nickname,
                            "photo": user.photo.url if user.photo.url else user.photo,
                        },
                    },
                }
            )
        else:
            return Response({"message": "Invalid request."}, status=400)

    @permission_classes([IsAuthenticated])
    def put(self, request):
        user = request.user
        if user.id is not None:
            check_serializer = AccountUpdateSerializer(
                data=request.data, context={"user": request.user}
            )

            # user update 입력값 체크
            if check_serializer.is_valid(raise_exception=True):
                serializer = AccountUpdateSerializer(
                    instance=user,
                    data=request.data,
                    partial=True,
                    context={"user": request.user},
                )
                # user update 진행
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(check_serializer.errors, status=status.HTTP_201_CREATED)

        return Response(
            {"message": "잘못된 접근입니다."}, status=status.HTTP_400_BAD_REQUEST
        )

    @permission_classes([IsAuthenticated])
    def delete(self, request):
        user = request.user

        if user.id is not None and user.is_active:
            user.delete()
            data = {"message": "user deleted."}

            # ++ 토큰은 어떻게 처리?
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "잘못된 접근입니다."}, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def token(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response(
            {"message": "잘못된 접근입니다."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return JsonResponse(
            {
                "id": user.id,
                "user_id": user.user_id,
                "email": user.email,
                "nickname": user.nickname,
                "age": user.age,
                "photo": user.photo.url if user.photo else "",
                "steamId": user.steamId,
            },
            status=status.HTTP_200_OK,
        )
    except AuthenticationFailed:
        return Response(
            {"message": "잘못된 접근입니다."}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
def refresh(request):
    refresh_token = request.data.get("refresh_token")
    if not refresh_token:
        return Response({"message": "Refresh token이 없습니다."}, status=400)

    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)  # 새 Access Token 발급
        return Response({"access_token": access_token}, status=200)
    except TokenError:
        return Response({"message": "유효하지 않은 Refresh token입니다."}, status=400)


@api_view(["GET"])
def interest(request):
    interests = Interest.objects.all()
    print(interests)
    serializer = InterestSerializer(interests, many=True)

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def steam_profile(request):
    user = request.user
    if user and user.steamId != None and user.steamId != "":
        data = {}

        api_url = "https://api.steampowered.com/IPlayerService/GetAnimatedAvatar/v1/"

        try:
            env = environ.Env()
            api_key = env("STEAM_API_KEY")
            params = {"key": api_key, "steamid": user.steamId}

            response = requests.get(api_url, params=params)

            response_data = response.json()["response"]
            print("test", response.status_code == 200 and response_data["avatar"] != {})
            # 요청 성공 여부 확인
            if response.status_code == 200 and response_data["avatar"] != {}:
                if response_data["avatar"] != None and response_data["avatar"] != "":
                    data["steam_photo"] = response_data["avatar"]["image_small"]
                    user.photo = response_data["avatar"]["image_small"]
                    user.save()
            else:
                api_url = (
                    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
                )
                params = {"key": api_key, "steamids": user.steamId}

                response = requests.get(api_url, params=params)

                # 요청 성공 여부 확인
                response_data = response.json()["response"]
                print(response_data, response.status_code)
                if response.status_code == 200:
                    if (
                        response_data["players"]
                        and response_data["players"][0]
                        and response_data["players"][0]["avatarfull"]
                    ):
                        data["steam_photo"] = response_data["players"][0]["avatarfull"]
                        user.photo = response_data["players"][0]["avatarfull"]
                        user.save()

        except requests.exceptions.RequestException as e:
            print(e)
            return Response({"message": "Invalid request."}, status=400)

        return JsonResponse(
            {
                "message": "Steam Animated Avatar",
                "data": data,
            }
        )
    else:
        return Response({"message": "Invalid request."}, status=400)


@api_view(["GET"])
def steam_login(request):
    user_id = request.query_params.get("user_id")
    page = request.query_params.get("page")

    steam_openid_url = "https://steamcommunity.com/openid/login"
    # 공통 파라미터
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.mode": "checkid_setup",
        "openid.realm": "http://localhost:5173/",  # Realm은 API를 호출한 도메인
    }

    # user_id가 있을 경우: 마이페이지로 리디렉션
    if page == "mypage" and user_id:
        params["openid.return_to"] = (
            f"http://localhost:5173/steam/callback?user_id={user_id}&page={page}"
        )
    # user_id가 없을 경우: 회원가입 페이지 or 로그인 페이지로 리디렉션
    else:
        params["openid.return_to"] = (
            f"http://localhost:5173/steam/callback?page={page}"  # 회원가입 페이지로 리디렉션
        )

    param_string = parse.urlencode(params)
    auth_url = steam_openid_url + "?" + param_string
    return JsonResponse({"auth_url": auth_url})


@api_view(["POST"])
def steam_callback(request):
    body = json.loads(request.data["body"])
    steam_id = body.get("steamId")
    user_id = body.get("userId")
    page = body.get("page")
    print(steam_id, user_id)
    # 'openid.claimed_id'가 존재하는 경우, 스팀 ID 추출
    if steam_id:
        if user_id and page == "mypage":
            if Account.objects.filter(steamId=steam_id).count() > 0:
                return Response({"message": "이미 연동된 스팀ID입니다."}, status=400)
            try:
                
                account = Account.objects.get(user_id=user_id)
                account.steamId = steam_id
                account.save()

                # DB에 리뷰공개 여부/플레이타임/리뷰 데이터 동기화
                sync_new_steam_user_data(account)

                return JsonResponse(
                    {
                        "message": "Steam ID linked successfully!",
                        "page":"mypage",
                        "user_id": account.id
                    }
                )
            except Account.DoesNotExist:
                return JsonResponse({"error": "Account not found"}, status=404)
        else:
            if page == "signin":
                try:
                    user = Account.objects.get(steamId=steam_id)
                except ObjectDoesNotExist:
                    return Response({"message": "계정을 찾을 수 없습니다."}, status=400)
                if not user:
                    return Response({"message": "잘못된 로그인 정보입니다."}, status=400)
                # 인증 성공: Token 발급 (or JWT 발급)
                login(request, user)  # 사용자 세션 생성
                refresh = RefreshToken.for_user(user)

                # 응답 반환
                return Response(
                    {
                        "message": "Login successful.",
                        "refresh_token": str(refresh),
                        "access_token": str(refresh.access_token),
                        "page":"signin",
                        "user": {
                            "id": user.id,
                            "user_id": user.user_id,
                            "email": user.email,
                            "nickname": user.nickname,
                            "age": user.age,
                            "photo": user.photo.url if user.photo else "",
                            "steamId": user.steamId,
                        },
                        # "token": token.key,
                    },
                    status=status.HTTP_200_OK,
                )
                
            if page == "signup":
                if Account.objects.filter(steamId=steam_id).count() > 0:
                    return JsonResponse({"error": "이미 가입된 스팀ID입니다."}, status=400)
                else:
                    return JsonResponse(
                        {
                            "message": "스팀 회원가입 진행", 
                            "page":"signup", 
                            "steam_id": steam_id
                        },status=status.HTTP_200_OK)
            
    return JsonResponse({"error": "Invalid method"}, status=405)


class BlockedUserAPIView(APIView):
    """
    차단된 유저 관련 API 뷰
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """차단된 유저 목록 반환"""
        blocked_users = Block.objects.filter(blocker=request.user).select_related(
            "blocked_user"
        )

        # 차단된 유저가 없을 때의 응답 처리
        if not blocked_users.exists():
            return Response(
                {"message": "차단한 유저가 없습니다."}, status=status.HTTP_200_OK
            )

        # 차단된 유저가 있을 때의 응답 처리
        data = [
            {
                "id": block.blocked_user.id,
                "nickname": block.blocked_user.nickname,
            }
            for block in blocked_users
        ]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """유저 차단"""
        blocked_user_id = request.data.get("blocked_user_id")
        blocked_user = get_object_or_404(Account, id=blocked_user_id)

        # 본인이 본인을 차단하려는 경우 방지
        if blocked_user == request.user:
            return Response(
                {"message": "본인을 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 차단 생성
        block, created = Block.objects.get_or_create(
            blocker=request.user, blocked_user=blocked_user
        )
        if not created:
            return Response(
                {"message": "이미 차단된 사용자입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "유저를 차단했습니다."}, status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        """유저 차단 해제"""
        blocked_user_id = request.data.get("blocked_user_id")
        blocked_user = get_object_or_404(Account, id=blocked_user_id)

        # 차단 해제
        deleted, _ = Block.objects.filter(
            blocker=request.user, blocked_user=blocked_user
        ).delete()
        if not deleted:
            return Response(
                {"message": "차단된 유저가 아닙니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "유저 차단을 해제했습니다."}, status=status.HTTP_204_NO_CONTENT
        )


class NoticeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자의 알림 목록 반환"""
        notices = Notice.objects.filter(user_id=request.user).order_by("-created_at")
        serializer = NoticeSerializer(notices, many=True)
        return Response(serializer.data)

    def delete(self, request):
        """읽은 알림 삭제"""
        Notice.objects.filter(user_id=request.user, is_read=True).delete()
        return Response(
            {"message": "확인한 알림은 삭제됩니다."}, status=status.HTTP_204_NO_CONTENT
        )


class NoticeDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notice_id):
        """알림 읽음 처리"""
        notice = get_object_or_404(Notice, id=notice_id, user_id=request.user)
        notice.is_read = True
        notice.save()
        return Response(
            {"message": "알림이 읽음 처리되었습니다."}, status=status.HTTP_200_OK
        )


class FriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자가 받은 친구 요청 목록 반환"""
        friend_requests = FriendRequest.objects.filter(
            friend_id=request.user, type=0
        )  # 대기 중 상태만
        serializer = serializers.FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)

    def post(self, request):
        """친구 요청 생성"""
        friend_id = request.data.get("friend_id")
        friend = get_object_or_404(Account, id=friend_id)

        if friend == request.user:
            return Response(
                {"message": "본인에게 친구 요청을 보낼 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 이미 친구인 경우
        if Friend.objects.filter(user_id=request.user, friend_id=friend).exists():
            return Response(
                {"message": "이미 친구입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 새로운 요청 생성
        friend_request, created = FriendRequest.objects.get_or_create(
            user_id=request.user,
            friend_id=friend,
            defaults={"type": 0},  # 대기 상태로 생성
        )

        if not created:
            return Response(
                {"message": "이미 대기 중인 친구 요청이 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 알림 생성
        Notice.objects.create(
            user_id=friend,
            type=Notice.TYPE_FRIEND_REQUEST,  # 친구 요청 알림 타입 (2)
            content=f"{request.user.nickname}님이 친구 요청을 보냈습니다.",
        )

        serializer = serializers.FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        """친구 요청 상태 변경 (수락/거절)"""
        friend_request_id = request.data.get("friend_request_id")
        new_type = request.data.get("type")  # 1: 수락, -1: 거절

        if new_type not in [1, -1]:
            return Response(
                {"message": "유효하지 않은 상태 값입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 요청 객체 가져오기
        friend_request = get_object_or_404(
            FriendRequest, id=friend_request_id, friend_id=request.user
        )

        if new_type == 1:  # 수락 상태
            # 친구 관계 생성
            Friend.objects.create(
                user_id=request.user, friend_id=friend_request.user_id
            )
            Friend.objects.create(
                user_id=friend_request.user_id, friend_id=request.user
            )
            # 요청 삭제
            friend_request.delete()
            return Response(
                {"message": "친구 요청을 수락하고 친구 관계가 생성되었습니다."},
                status=status.HTTP_200_OK,
            )

        if new_type == -1:  # 거절 상태
            # 요청 삭제
            friend_request.delete()
            return Response(
                {"message": "친구 요청을 거절하고 삭제했습니다."},
                status=status.HTTP_204_NO_CONTENT,
            )


class FriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """친구 목록 조회"""
        friends = Friend.objects.filter(user_id=request.user).select_related(
            "friend_id"
        )
        data = [
            {
                "id": friend.friend_id.id,
                "nickname": friend.friend_id.nickname,
                "photo": friend.friend_id.photo.url if friend.friend_id.photo else None,
            }
            for friend in friends
        ]
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request):
        """친구 삭제"""
        friend_id = request.data.get("friend_id")
        friend = get_object_or_404(Friend, user_id=request.user, friend_id=friend_id)

        # 친구 관계 삭제 (양방향)
        Friend.objects.filter(user_id=request.user, friend_id=friend_id).delete()
        Friend.objects.filter(user_id=friend_id, friend_id=request.user).delete()

        return Response(
            {"message": "친구가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )
