from rest_framework import serializers
from .models import Account
from django.contrib.auth.hashers import make_password  # 비밀번호 해싱
from django.core.validators import validate_email
import re


class AccountSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(
        required=True, error_messages={"required": "유저 아이디 입력은 필수입니다."}
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "이메일 값은 필수입니다.",
            "invalid": "올바른 이메일 형식으로 입력해주세요.",
        },
    )
    nickname = serializers.CharField(
        required=True, error_messages={"required": "닉네임은 입력은 필수입니다."}
    )
    age = serializers.IntegerField(
        required=True, error_messages={"required": "나이 입력은 필수입니다."}
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={"required": "비밀번호 입력은 필수입니다."},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 재입력은 필수입니다.",
        },
    )

    def validate(self, data):
        # 비밀번호와 확인용 비밀번호가 일치하는지 검증
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"message": "비밀번호가 일치하지 않습니다."}
            )
        if Account.objects.filter(user_id=data["user_id"]).exists():
            raise serializers.ValidationError(
                {"message": "이미 사용중인 아이디 입니다."}
            )
        elif re.match(r"[^@]+@[^@]+\.[^@]+", data["user_id"]):
            raise serializers.ValidationError(
                {"message": "아이디는 이메일 형식을 지원하지 않습니다."}
            )
        if Account.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"message": "이미 사용중인 이메일 입니다."}
            )
        if Account.objects.filter(nickname=data["nickname"]).exists():
            raise serializers.ValidationError(
                {"message": "이미 사용중인 닉네임 입니다."}
            )
        return data

    class Meta:
        model = Account
        fields = (
            "user_id",
            "password",
            "confirm_password",
            "email",
            "age",
            "nickname",
            "photo",
        )

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)


class PasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["password"]

    def save(self, **kwargs):
        user = self.context.get("user")
        password = self.validated_data["password"]
        user.set_password(password)  # 비밀번호 해싱 및 저장
        user.save()
        return user


class AccountDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


class AccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "email",
            "name",
            "nickname",
            "birth_date",
            "bio",
            "gender",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "name": {"required": True},
            "nickname": {"required": True},
            "birth_date": {"required": True},
            "bio": {"required": False},
            "gender": {"required": False},
        }

    def validate_email(self, value):
        user = self.context.get("user")
        email = user.email
        if value != email:
            if (
                Account.objects.exclude(id=user.id).filter(username=value).exists()
                or Account.objects.filter(email=value).exists()
            ):
                raise serializers.ValidationError(
                    "This email already taken by another user."
                )

        return value
