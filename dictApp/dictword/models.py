from django.db import models
from django.contrib.auth.models import User
from django.db.models.base import Model

# Create your models here.
class Dictword(models.Model):
    user = models.ManyToManyField(User)
    word = models.CharField(max_length=50)
    definition = models.TextField()
    part_of_speech = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.word

class Score(models.Model):
    user = models.ForeignKey( User, on_delete=models.CASCADE)
    word = models.ForeignKey( Dictword, on_delete=models.CASCADE)
    points = models.IntegerField()
    
    def __str__(self):
        return self.user.username + " - " + self.word.word