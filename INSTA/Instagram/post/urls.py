from django.contrib import admin
from django.urls import path
from post import views


urlpatterns = [
    path('<int:slug>' , views.showPost, name='showPost'), #POST A PHOTO
    path('likepostpage', views.likepost,  name='likepostpage'), #Show user's timeline 
]   
   