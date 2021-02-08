from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Dictword(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    word = models.CharField(max_length=50)
    definition = models.CharField(max_length=200)
    partOfSpeech = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.word