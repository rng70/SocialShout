from django.shortcuts import render, HttpResponse

# Create your views here.

def showProfile(request, slug):
    user_id = slug
    return render(request, 'userprofile/profile.html')