import cx_Oracle
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages



# Create your views here.
def loginhome(request):
    return render(request,'account/login.html')
  
def signup(request):
    return render(request,'account/signup.html')


def handleSignUp(request):
    if(request.method == 'POST'):
        username = request.POST['username']
        fullname= request.POST['fullname']
        email= request.POST['email']
        password= request.POST['password']
        password2= request.POST['password2']
        birthdate = request.POST['birthdate']
        male = request.POST.get('male', False)
        if(male): 
            gender = 'male'
        else :
            gender = 'female'

        #check for errorneous input
        if(not username.isalnum()):
            messages.error(request, 'Username should only contain letters and numbers!')
            return redirect('/signup')
        if(password != password2):
            messages.error(request, "Passwords didn't matched")
            return redirect('/signup')     
        
        #Create the  user in database
        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        conn = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)
        c = conn.cursor()

        cmnd ="""
        INSERT INTO USERACCOUNT (USER_NAME,FULL_NAME,EMAIL,PASSWORD,GENDER, DATE_OF_BIRTH)
        VALUES(:username, :fullname, :email, :password,:gender,  to_date(:birthday, 'yyyy-mm-dd')) 
        """
        c.execute(cmnd, [username,fullname, email, password, gender, birthdate] )
        conn.commit()
        conn.close()
        
        myuser = User.objects.create_user(username=username, password=password)
        myuser.save()
        messages.success(request, 'Your Account Has  successfully been created!')
            
        return redirect('/home')

    else :
        return HttpResponse('404 - Not Found')



def handleLogin(request):
    if(request.method=='POST'):
        loginUsername=request.POST['loginUsername']
        loginPassword=request.POST['loginPassword']

        user = authenticate(username = loginUsername, password=loginPassword)

        if(user is not None):
            login(request, user)
            messages.success(request, "Successfully Logged In!")
            print(user.username)
            
            return redirect('/home')
        else :
            messages.error(request, 'Invalid User!')
            return redirect('/')
    else :
        return HttpResponse('404 - Not Found')

def handleLogout(request):
    messages.success(request, "Successfully logged out!")
    logout(request)
    return redirect('/')