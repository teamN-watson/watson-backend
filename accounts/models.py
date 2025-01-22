from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from accounts.utils import OverwriteStorage, rename_imagefile_to_uid
from django.conf import settings
from django.db.models import Q


class Game(models.Model):
    db_table = "accounts_game"
    appID = models.IntegerField(unique=True, db_index=True)  # Steam App ID
    name = models.CharField(max_length=255)  # 게임 이름
    release_date = models.CharField(max_length=100)
    required_age = models.IntegerField(default=0)
    price = models.FloatField(default=0.0)
    header_image = models.URLField(max_length=300)
    windows = models.BooleanField(default=False)
    mac = models.BooleanField(default=False)
    linux = models.BooleanField(default=False)
    metacritic_score = models.IntegerField(default=0)
    metacritic_url = models.URLField(max_length=300, blank=True)
    supported_languages = models.JSONField(default=list)
    categories = models.JSONField(default=list)
    genres = models.JSONField(default=list)  # 장르 (JSON 형식으로 저장)
    genres_kr = models.JSONField(default=list)  # 한글로 변환된 장르
    screenshots = models.JSONField(default=list)
    movies = models.JSONField(default=list)
    estimated_owners = models.CharField(max_length=100)
    median_playtime_forever = models.IntegerField(default=0)
    tags = models.JSONField(default=dict)

    def __str__(self):
        return self.name

class Tag(models.Model):  # 게임의 태그
    name_en = models.CharField(max_length=50, unique=True)
    name_ko = models.CharField(max_length=20, unique=True)
    steam_tag_id = models.IntegerField(default=0)


class Interest(models.Model):  # 게임
    name = models.CharField(max_length=10, unique=True)
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
    steamId = models.CharField(max_length=30, blank=True)
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
    
    def get_steam_tag_names_en(self):
        """
        4단계로 태그 정보를 추출합니다:
        1. AccountInterest에서 interest_id 목록 추출
        2. InterestTag에서 tag_id 목록 추출
        3. Tag에서 steam_tag_id 목록 추출
        4. Tag에서 steam_tag_id에 해당하는 name_en 목록 추출
        """
        # 1단계: AccountInterest에서 interest_id 목록 추출
        interest_ids = AccountInterest.objects.filter(
            account=self
        ).values_list('interest_id', flat=True)

        # 2단계: InterestTag에서 tag_id 목록 추출
        tag_ids = InterestTag.objects.filter(
            interest_id__in=interest_ids
        ).values_list('tag_id', flat=True)

        # 3단계: Tag에서 steam_tag_id 목록 추출
        steam_tag_ids = Tag.objects.filter(
            id__in=tag_ids
        ).exclude(
            steam_tag_id=0
        ).values_list('steam_tag_id', flat=True).distinct()

        # 4단계: steam_tag_id에 해당하는 name_en 목록 추출
        return list(Tag.objects.filter(
            steam_tag_id__in=steam_tag_ids
        ).values_list('name_en', flat=True).distinct())


class Notice(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    TYPE_GENERAL = 1
    TYPE_FRIEND_REQUEST = 2
    TYPE_COMMENT = 3

    TYPE_CHOICES = [
        (TYPE_GENERAL, "일반 알림"),
        (TYPE_FRIEND_REQUEST, "친구 요청 알림"),
        (TYPE_COMMENT, "댓글 알림"),
    ]

    type = models.IntegerField(choices=TYPE_CHOICES, default=0)
    content = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)  # 읽음 여부
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FriendRequest(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_friend_request",
    )
    friend_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.IntegerField(default=0)  # 0: 대기중, 1: 수락, -1: 거절
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Friend(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="my_friends"
    )
    friend_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SteamProfile(models.Model):
    """
    Account의 steamId를 연동한 스팀 프로필 기본 정보
    리뷰와 플레이 타임 표시 여부 등을 저장한다
    """

    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    is_review = models.BooleanField(default=False)  # 리뷰 공개 여부
    is_playtime = models.BooleanField(default=False)  # 플레이 타임 공개 여부


class SteamReview(models.Model):
    """
    스팀 리뷰 중에서 'Recommended'가 붙은 상위 3개를 저장할 모델
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    app_id = models.CharField(max_length=50)  # 게임 앱 아이디
    # review_text = models.TextField(blank=True)  # 필요 시 리뷰 내용을 저장


class SteamPlaytime(models.Model):
    """
    플레이 타임 상위 2개 게임 정보를 저장할 모델
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    app_id = models.CharField(max_length=50)


class Block(models.Model):
    """
    유저 차단 정보를 저장할 모델
    """

    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_users",  # 차단한 유저
    )
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by_users",  # 차단된 유저
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("blocker", "blocked_user")]
        ordering = ["-created_at"]
