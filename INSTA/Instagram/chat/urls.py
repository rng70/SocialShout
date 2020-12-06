from django.contrib import admin
from django.urls import path
from chat import views


urlpatterns = [
    # show message list
    path('chatlist', views.showChatList, name='showChatlist'),
    # show a particular post
    path('<int:to_id>', views.showChat, name='showchat'),
    path('send/<int:to_id>', views.send, name='send'),  # show a particular post
]
