from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    email = models.CharField(max_length=32, null=True, blank=True)
    phone = models.CharField(max_length=11, null=True, blank=True)
    balance = models.FloatField(default=100.0)