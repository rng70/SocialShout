from django.contrib import admin
from django.urls import path
from notifications import views


urlpatterns = [
    path('', views.showNotifications, name='showNotifications'), #show users notifications page 
    path('check/<int:notification_id>', views.checkNoification, name='checkNotification'), #check that noti. when clicking
]
