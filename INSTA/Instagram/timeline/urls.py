from django.contrib import admin
from django.urls import path
from timeline import views


urlpatterns = [
    path('post' , views.post, name='post'), #POST A PHOTO
    path('likepost', views.likepost,  name='likepost'), #Show user's timeline 
    path('search', views.search,  name='searchuser'), #Show search results 
    path('', views.home,  name='home'), #Show user's timeline 
]   
   
    
