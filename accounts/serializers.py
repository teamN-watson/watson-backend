from rest_framework import serializers
from .models import Account, Interest, Notice
from django.contrib.auth.hashers import make_password  # 비밀번호 해싱
from django.core.validators import validate_email
import re


class SignupStep1Serializer(serializers.ModelSerializer):
    user_id = serializers.CharField(
        required=True,
        error_messages={
            "required": "유저 아이디 입력은 필수입니다.",
            "blank": "아이디를 입력해주세요.",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 입력은 필수입니다.",
            "blank": "비밀번호를 입력해주세요.",
        },
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 재입력은 필수입니다.",
            "blank": "비밀번호를 재입력해주세요.",
        },
    )

    def validate(self, data):
        errors = {}

        # 비밀번호와 확인용 비밀번호가 일치하는지 검증
        if data["password"] != data["confirm_password"]:
            errors["confirm_password"] = ["비밀번호가 일치하지 않습니다."]
        # 이미 사용 중인 아이디가 있는지 확인
        if Account.objects.filter(user_id=data["user_id"]).exists():
            errors["user_id"] = ["이미 사용중인 아이디 입니다."]
        # 아이디가 이메일 형식을 지원하지 않는지 확인
        elif re.match(r"[^@]+@[^@]+\.[^@]+", data["user_id"]):
            errors["user_id"] = ["아이디는 이메일 형식을 지원하지 않습니다."]
        # 유효성 검사 후 에러가 있으면 ValidationError를 발생시킴
        if errors:
            raise serializers.ValidationError(errors)

        return data

    class Meta:
        model = Account
        fields = (
            "user_id",
            "password",
            "confirm_password",
            "photo",
        )


class SignupStep2Serializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "이메일 값은 필수입니다.",
            "invalid": "올바른 이메일 형식으로 입력해주세요.",
            "blank": "이메일를 입력해주세요.",
        },
    )
    nickname = serializers.CharField(
        required=True,
        error_messages={
            "required": "닉네임은 입력은 필수입니다.",
            "blank": "닉네임을 입력해주세요.",
        },
    )
    age = serializers.IntegerField(
        required=True,
        error_messages={
            "required": "나이 입력은 필수입니다.",
            "invalid": "올바른 나이를 입력해주세요.",
            "blank": "나이를 입력해주세요.",
        },
    )

    def validate(self, data):
        errors = {}

        # 이미 사용 중인 이메일이 있는지 확인
        if Account.objects.filter(email=data["email"]).exists():
            errors["email"] = ["이미 사용중인 이메일 입니다."]

        # 이미 사용 중인 닉네임이 있는지 확인
        if Account.objects.filter(nickname=data["nickname"]).exists():
            errors["nickname"] = ["이미 사용중인 닉네임 입니다."]

        # 유효성 검사 후 에러가 있으면 ValidationError를 발생시킴
        if errors:
            raise serializers.ValidationError(errors)

        return data

    class Meta:
        model = Account
        fields = (
            "email",
            "age",
            "nickname",
        )


class AccountSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(
        required=True,
        error_messages={
            "required": "유저 아이디 입력은 필수입니다.",
            "blank": "아이디를 입력해주세요.",
        },
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "이메일 값은 필수입니다.",
            "invalid": "올바른 이메일 형식으로 입력해주세요.",
            "blank": "이메일를 입력해주세요.",
        },
    )
    nickname = serializers.CharField(
        required=True,
        error_messages={
            "required": "닉네임은 입력은 필수입니다.",
            "blank": "닉네임을 입력해주세요.",
        },
    )
    age = serializers.IntegerField(
        required=True,
        error_messages={
            "required": "나이 입력은 필수입니다.",
            "invalid": "올바른 나이를 입력해주세요.",
            "blank": "나이를 입력해주세요.",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 입력은 필수입니다.",
            "blank": "비밀번호를 입력해주세요.",
        },
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "비밀번호 재입력은 필수입니다.",
            "blank": "비밀번호를 재입력해주세요.",
        },
    )

    def validate(self, data):
        errors = {}

        # 비밀번호와 확인용 비밀번호가 일치하는지 검증
        if data["password"] != data["confirm_password"]:
            errors["confirm_password"] = ["비밀번호가 일치하지 않습니다."]

        # 이미 사용 중인 아이디가 있는지 확인
        if Account.objects.filter(user_id=data["user_id"]).exists():
            errors["user_id"] = ["이미 사용중인 아이디 입니다."]
        # 아이디가 이메일 형식을 지원하지 않는지 확인
        elif re.match(r"[^@]+@[^@]+\.[^@]+", data["user_id"]):
            errors["user_id"] = ["아이디는 이메일 형식을 지원하지 않습니다."]

        # 이미 사용 중인 이메일이 있는지 확인
        if Account.objects.filter(email=data["email"]).exists():
            errors["email"] = ["이미 사용중인 이메일 입니다."]

        # 이미 사용 중인 닉네임이 있는지 확인
        if Account.objects.filter(nickname=data["nickname"]).exists():
            errors["nickname"] = ["이미 사용중인 닉네임 입니다."]

        # 유효성 검사 후 에러가 있으면 ValidationError를 발생시킴
        if errors:
            raise serializers.ValidationError(errors)

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
            "steamId",
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

    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "age",
            "nickname",
            "photo",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "email": {"required": True},
            "age": {"required": True},
            "nickname": {"required": True},
            "photo": {"required": False},
        }

    def validate_email(self, value):
        user = self.context.get("user")
        email = user.email
        if value != email:
            if Account.objects.filter(email=value).exists():
                raise serializers.ValidationError("해당 이메일은 이미 사용중입니다.")

        return value


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ["id", "name"]  # 모든 필드를 직렬화


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['id', 'type', 'content', 'is_read', 'created_at', 'updated_at']