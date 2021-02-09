from django.contrib import admin
from django.urls import path
from . import views as home_views

urlpatterns = [
    path('', home_views.home, name='home'),
    path('practice', home_views.practice, name='practice'),
]