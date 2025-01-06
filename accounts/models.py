from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from accounts.utils import OverwriteStorage, rename_imagefile_to_uid


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

    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS = ["email", "age"]

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.user_id
