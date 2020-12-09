from django.contrib import admin
from django.urls import path
from post import views


urlpatterns = [
    path('<int:slug>' , views.showPost, name='showPost'), #show a particular post
    path('likepostpage', views.likepost,  name='likepostpage'), #like dislike the post in postpage

    #API's to post a comment
    path('postComment/<int:slug>' , views.postComment, name='postComment'),

    path('edit/<int:postid>' , views.editpost, name='editpost') ,#edit post 
    path('saveEdited/<int:postid>' , views.saveEditedPost, name='saveEditedpost'), # save the edited post 

    path('addtag/<int:postid>' , views.addtag, name='addTag'), #adds tagged people name in taglist of post
    path('autocomplete/<int:postid>', views.autocomplete, name='autocomplete'),#live search while typing taglist

    path('delete/<int:postid>', views.deleltePost, name='deletepost'), #delete post 

    path('removetag/<int:postid>', views.removetag, name='removetag'), #removes tag  
]   
   