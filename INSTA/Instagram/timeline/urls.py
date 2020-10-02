from django.contrib import admin
from django.urls import path
from timeline import views


urlpatterns = [
    path('', views.home,  name='home'),
]
