from django.db import models
from django.contrib.auth.models import AbstractUser

from django.utils.translation import gettext_lazy as _

# for memCached
import datetime
from django.core.cache import cache
from django.conf import settings


# Create your models here.

class User(AbstractUser):
    email = models.EmailField(_('email'), unique=True, blank=False)
    full_name = models.CharField(_('full_name'), max_length=200, null=True)
    phone = models.IntegerField(_('phone'), null=True)

    gender_choice = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(_('gender'), max_length=10, choices=gender_choice, null=True, blank=True)

    account_choice = (
        ('User', 'User'),
        ('Business', 'Business')
    )
    account_type = models.CharField(_('account_type'), max_length=50, choices=account_choice, default='User')

    def __str__(self):
        return self.username

