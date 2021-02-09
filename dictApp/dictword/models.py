from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Dictword(models.Model):
    user = models.ManyToManyField(User)
    word = models.CharField(max_length=50)
    definition = models.CharField(max_length=100)
    part_of_speech = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.word

class Interaction(models.Model):
    user = models.ForeignKey( User, on_delete=models.CASCADE)
    word = models.ForeignKey( Dictword, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    search_count = models.IntegerField(default=0)
    appear_count = models.IntegerField(default=0)
    power = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username + " - " + self.word.word