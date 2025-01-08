from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from .models import Account

from .serializers import (
    AccountDeleteSerializer,
    AccountSerializer,
    AccountUpdateSerializer,
    LoginSerializer,
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


@api_view(["POST"])
def signup(request):
    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        # 인증 성공: Token 발급 (or JWT 발급)

        user = authenticate(
            request,
            user_id=request.data["user_id"],
            password=request.data["password"],
        )
        refresh = RefreshToken.for_user(user)

        # 응답 반환
        return Response(
            {
                "message": "회원가입 되었습니다.",
                "data": {
                    "refreshToken": str(refresh),
                    "accessToken": str(refresh.access_token),
                    "user": serializer.data,
                },
            },
            status=status.HTTP_201_CREATED,
        )


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
                "data": {
                    "refreshToken": str(refresh),
                    "accessToken": str(refresh.access_token),
                    "user": {
                        "user_id": user.user_id,
                        "email": user.email,
                        "nickname": user.nickname,
                    },
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
        refresh_token = RefreshToken(request.data["refreshToken"])
        refresh_token.blacklist()

        return Response({"message": "Successfully logged out."}, status=200)
    except TokenError:
        return Response({"message": "Invalid refresh token."}, status=400)


class MypageAPIView(APIView):

    @permission_classes([IsAuthenticated])
    def get(self, request):
        if request.user:
            reviews = request.user.reviews.all()
            reviews_data = ReviewSerializer(reviews, many=True).data
            profile_data = AccountSerializer(request.user).data

            return JsonResponse(
                {
                    "message": "You are authenticated",
                    "data": {
                        "reviews": reviews_data,
                        "profile": profile_data,
                        "friends": {},
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
