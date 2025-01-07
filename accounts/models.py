from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from accounts.utils import OverwriteStorage, rename_imagefile_to_uid
from django.conf import settings


class Tag(models.Model):  # 게임의 태그
    name = models.CharField(max_length=50, unique=True)
    steam_tag_id = models.IntegerField(default=0)


class Interest(models.Model):  # 게임
    title = models.CharField(max_length=10, unique=True)
    tags = models.ManyToManyField(Tag, through="InterestTag", related_name="tags")


class InterestTag(models.Model):  # 게임과 태그의 관계 설정
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["interest", "tag"], name="unique_interest_tag"
            )
        ]


class AccountInterest(models.Model):  # 게임과 유저의 관계 설정
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "interest"], name="unique_account_interest"
            )
        ]


class AccountManager(BaseUserManager):
    def create_user(self, user_id, email, password, nickname, age, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(
            user_id=user_id, email=email, nickname=nickname, age=age, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, email, password, nickname, age, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(user_id, email, password, nickname, age, **extra_fields)

    def get_by_natural_key(self, user_id):
        return self.get(user_id=user_id)


class Account(AbstractBaseUser):
    user_id = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=30, blank=True)
    age = models.IntegerField(default=0)
    photo = models.ImageField(
        upload_to=rename_imagefile_to_uid, storage=OverwriteStorage(), blank=True
    )
    interests = models.ManyToManyField(
        Interest, through="AccountInterest", related_name="interests"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS = ["email", "age", "nickname"]

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.user_id


class Notice(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    type = models.IntegerField(default=0)
    content = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FriendRequest(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_friend_request",
    )
    friend_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Friend(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="my_friends"
    )
    friend_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
