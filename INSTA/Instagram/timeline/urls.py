from django.contrib import admin
from django.urls import path
from timeline import views


urlpatterns = [
    path('post' , views.post, name='post'), #POST PHOTO
    path('', views.home,  name='home'),
]
   
    
