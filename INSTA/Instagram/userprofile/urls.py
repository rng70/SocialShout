from django.contrib import admin
from django.urls import path
from userprofile import views


urlpatterns = [
    path('<int:userid>' , views.showProfile, name='showProfile'), #show a user's profile page
    path('<str:username>' , views.showProfileByName, name='showProfileByNmae'), #show a user's profile page 
    
    path("follow/<int:userid>", views.follow, name="follow"), #handling the follow unfollow
    path("followers/<int:userid>", views.showFollowers, name="showFollowers"), #showing the followers list
    path("followings/<int:userid>", views.showFollowings, name="showFollowings"), #showing the followings list

    path('edit/<int:userid>', views.editProfile, name="editProfile"),
    path('savaPersonalInfo/<int:userid>', views.savePersonalInfo, name="savePersonalInfo"),
    path('changeProfilePic/<int:userid>', views.changeProfilePic, name="changeProfilePic"),
]   
  