from django.conf.urls import url
from . import views
from django.urls import path

app_name = 'game'

urlpatterns = [
    path(r'', views.index, name='gamelobby'),
]