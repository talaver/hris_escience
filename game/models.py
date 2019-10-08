from django.db import models

# Create your models here.


class Team(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=10)
    created_time = models.DateTimeField(auto_now_add=True)
    total_points = models.IntegerField()

    def __str__(self):
        return self.name

class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    team = models.IntegerField()
    points = models.IntegerField()
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Session(models.Model):
    player_count = models.IntegerField()
    team_count = models.IntegerField()



class GameMaster(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class

