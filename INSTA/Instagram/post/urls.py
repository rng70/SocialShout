from django.contrib import admin
from django.urls import path
from post import views


urlpatterns = [
    path('<int:slug>' , views.showPost, name='showPost'), #show a particular post
    path('likepostpage', views.likepost,  name='likepostpage'), #like dislike the post in postpage

    #API's to post a comment
    path('postComment/<int:slug>' , views.postComment, name='postComment')
]   
   