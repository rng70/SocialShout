from django.contrib import admin
from django.urls import path
from userprofile import views


urlpatterns = [
    path('<int:slug>' , views.showProfile, name='showProfile'), #show a user's profile page
    
]   
   