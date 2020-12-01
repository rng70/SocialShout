from django.contrib import admin
from django.urls import path
from chat import views


urlpatterns = [
     path('<int:to_id>' , views.showChat, name='showchat'), #show a particular post
     path('send/<int:to_id>' , views.send, name='send'), #show a particular post
   
]
