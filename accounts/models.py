from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from accounts.utils import OverwriteStorage, rename_imagefile_to_uid


class AccountManager(BaseUserManager):
    def create_user(self, user_id, email, password, nickname, age, **extra_fields):
        if not user_id:
            raise ValueError("The user_id field is required.")
        if not email:
            raise ValueError("The Email field is required.")
        if not password:
            raise ValueError("The Password field is required.")
        if not age:
            raise ValueError("The Age field is required.")
        # if not nickname:
        #     raise ValueError("The Nickname field is required.")

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

        return self.create_user(
            self, user_id, email, password, nickname, age, **extra_fields
        )


class Account(AbstractBaseUser):
    user_id = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=30, blank=True)
    age = models.IntegerField(default=0)
    photo = models.ImageField(
        upload_to=rename_imagefile_to_uid, storage=OverwriteStorage(), blank=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS = ["email", "age"]

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.user_id
