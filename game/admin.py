from django.contrib import admin
from .models import Player, Team, Session, GameMaster

# Register your models here.

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Session)
admin.site.register(GameMaster)
