from django.contrib import admin
from django.urls import path
from userprofile import views


urlpatterns = [
    path('<int:userid>' , views.showProfile, name='showProfile'), #show a user's profile page
    path('<str:username>' , views.showProfileByName, name='showProfileByNmae'), #show a user's profile page 
    
    path("follow/<int:userid>", views.follow, name="follow"), #handling the follow unfollow
    
]   
   