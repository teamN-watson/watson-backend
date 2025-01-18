from rest_framework.decorators import api_view
from rest_framework.views import APIView

from .models import (Account, 
                    AccountInterest, 
                    Interest, 
                    Block, 
                    Notice,
                    FriendRequest,
                    Friend,
                    )

from .serializers import (
    AccountDeleteSerializer,
    AccountSerializer,
    AccountUpdateSerializer,
    InterestSerializer,
    LoginSerializer,
    SignupStep1Serializer,
    SignupStep2Serializer,
    NoticeSerializer
)
from reviews.serializers import ReviewSerializer
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
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

from accounts import serializers


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
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
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
            serializer = AccountDeleteSerializer(
                instance=user, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                password = serializer.validated_data["password"]
                # 비밀번호가 동일한 경우 유저 삭제 진행
                if check_password(password, user.password):
                    user.delete()
                    data = {"message": "user deleted."}

                    # ++ 토큰은 어떻게 처리?
                    return Response(data, status=status.HTTP_200_OK)
                return Response(
                    {"message": "Password does not match."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
    if user_id:
        params["openid.return_to"] = (
            f"http://localhost:5173/steam/callback?user_id={user_id}"
        )
    # user_id가 없을 경우: 회원가입 페이지로 리디렉션
    else:
        params["openid.return_to"] = (
            "http://localhost:5173/signup?from_steam=true"  # 회원가입 페이지로 리디렉션
        )

    param_string = parse.urlencode(params)
    auth_url = steam_openid_url + "?" + param_string
    return JsonResponse({"auth_url": auth_url})


@api_view(["POST"])
def steam_callback(request):
    body = json.loads(request.data["body"])
    steam_id = body.get("steamId")
    user_id = body.get("userId")
    print(steam_id, user_id)
    # 'openid.claimed_id'가 존재하는 경우, 스팀 ID 추출
    if steam_id and user_id:
        try:
            account = Account.objects.get(user_id=user_id)
            account.steamId = steam_id
            account.save()

            return JsonResponse(
                {
                    "message": "Steam ID linked successfully!",
                    "data": {"user_id": account.id},
                }
            )
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
    return JsonResponse({"error": "Invalid method"}, status=405)


class BlockedUserAPIView(APIView):
    """
    차단된 유저 관련 API 뷰
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """차단된 유저 목록 반환"""
        blocked_users = Block.objects.filter(blocker=request.user).select_related('blocked_user')

        # 차단된 유저가 없을 때의 응답 처리
        if not blocked_users.exists():
            return Response({"message": "차단한 유저가 없습니다."}, status=status.HTTP_200_OK)

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
            return Response({"message": "본인을 차단할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 차단 생성
        block, created = Block.objects.get_or_create(blocker=request.user, blocked_user=blocked_user)
        if not created:
            return Response({"message": "이미 차단된 사용자입니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "유저를 차단했습니다."}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """유저 차단 해제"""
        blocked_user_id = request.data.get("blocked_user_id")
        blocked_user = get_object_or_404(Account, id=blocked_user_id)

        # 차단 해제
        deleted, _ = Block.objects.filter(blocker=request.user, blocked_user=blocked_user).delete()
        if not deleted:
            return Response({"message": "차단된 유저가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "유저 차단을 해제했습니다."}, status=status.HTTP_204_NO_CONTENT)


class NoticeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자의 알림 목록 반환"""
        notices = Notice.objects.filter(user_id=request.user).order_by('-created_at')
        serializer = NoticeSerializer(notices, many=True)
        return Response(serializer.data)

    def delete(self, request):
        """읽은 알림 삭제"""
        Notice.objects.filter(user_id=request.user, is_read=True).delete()
        return Response({"message": "확인한 알림은 삭제됩니다."}, status=status.HTTP_204_NO_CONTENT)


class NoticeDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notice_id):
        """알림 읽음 처리"""
        notice = get_object_or_404(Notice, id=notice_id, user_id=request.user)
        notice.is_read = True
        notice.save()
        return Response({"message": "알림이 읽음 처리되었습니다."}, status=status.HTTP_200_OK)
    

class FriendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자가 받은 친구 요청 목록 반환"""
        friend_requests = FriendRequest.objects.filter(friend_id=request.user, type=0)  # 대기 중 상태만
        serializer = serializers.FriendRequestSerializer(friend_requests, many=True)
        return Response(serializer.data)

    def post(self, request):
        """친구 요청 생성"""
        friend_id = request.data.get("friend_id")
        friend = get_object_or_404(Account, id=friend_id)

        if friend == request.user:
            return Response({"message": "본인에게 친구 요청을 보낼 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 이미 친구인 경우
        if Friend.objects.filter(user_id=request.user, friend_id=friend).exists():
            return Response({"message": "이미 친구입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 새로운 요청 생성
        friend_request, created = FriendRequest.objects.get_or_create(
            user_id=request.user, friend_id=friend,
            defaults={"type": 0}  # 대기 상태로 생성
        )

        if not created:
            return Response({"message": "이미 대기 중인 친구 요청이 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        """친구 요청 상태 변경 (수락/거절)"""
        friend_request_id = request.data.get("friend_request_id")
        new_type = request.data.get("type")  # 1: 수락, -1: 거절

        if new_type not in [1, -1]:
            return Response({"message": "유효하지 않은 상태 값입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 요청 객체 가져오기
        friend_request = get_object_or_404(FriendRequest, id=friend_request_id, friend_id=request.user)

        if new_type == 1:  # 수락 상태
            # 친구 관계 생성
            Friend.objects.create(user_id=request.user, friend_id=friend_request.user_id)
            Friend.objects.create(user_id=friend_request.user_id, friend_id=request.user)
            # 요청 삭제
            friend_request.delete()
            return Response({"message": "친구 요청을 수락하고 친구 관계가 생성되었습니다."}, status=status.HTTP_200_OK)

        if new_type == -1:  # 거절 상태
            # 요청 삭제
            friend_request.delete()
            return Response({"message": "친구 요청을 거절하고 삭제했습니다."}, status=status.HTTP_204_NO_CONTENT)
        
class FriendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """친구 목록 조회"""
        friends = Friend.objects.filter(user_id=request.user).select_related('friend_id')
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

        return Response({"message": "친구가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
