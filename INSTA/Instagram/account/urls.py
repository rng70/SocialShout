from django.contrib import admin
from django.urls import path
from account import views


urlpatterns = [
    path('', views.loginhome, name='login'), #loginPage
    path('signup', views.signup, name='signup'), #signUp page
    path('handleSignUp', views.handleSignUp, name='handleSignUp'), #validate signup input
    path('login', views.handleLogin, name='handleLogin'), #validate login input
    path('logout', views.handleLogout, name='handleLogout'), #to logout
]
