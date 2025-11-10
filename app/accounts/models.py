from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE)
    bio = models.TextField(max_length=500, blank=True)
