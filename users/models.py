from django.db import models
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
# from django.contrib.auth.models import AbstractUser

from .managers import UserManager

from django.db import models
import uuid


class BaseModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_on = models.DateTimeField(null=True, blank=True)


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    mobile = models.CharField(unique=True, max_length=14, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    user_pic = models.FileField(null=True, blank=True, upload_to='media/')

    def __str__(self):
        return f"{self.username}"

    class Meta:
        """A meta object for defining name of the user table"""
        db_table = "User"

    # use User manager to manage create user and super user
    objects = UserManager()

    # define required fields
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.created_at}'


class Friends(models.Model):
    user_1 = models.ForeignKey(User, related_name='friends_user_1', on_delete=models.CASCADE)
    user_2 = models.ForeignKey(User, related_name='friends_user_2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user_1.username} - {self.user_2.username}'

    class Meta:
        verbose_name_plural = "Friends"
