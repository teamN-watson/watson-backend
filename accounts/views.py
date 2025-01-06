from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .models import Account

from .serializers import AccountSerializer, LoginSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import AuthenticationFailed


# Create your views here.
@api_view(["POST"])
def signup(request):
    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(
            {"message": "회원가입 되었습니다.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


@api_view(["POST"])
def signin(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        # 입력 데이터에서 사용자 인증
        user_id = serializer.validated_data["user_id"]
        password = serializer.validated_data["password"]
        user = authenticate(request, user_id=user_id, password=password)
        if not user:
            account = get_object_or_404(Account, user_id=user_id)
            if account is not None and account.is_active is False:
                return Response(
                    {"message": "This user is deactivated"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            raise AuthenticationFailed("Invalid user_id or password.")

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
        return Response(
            {
                "message": "You are authenticated",
                "user_id": request.user.user_id,
            }
        )
