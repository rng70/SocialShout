import cx_Oracle
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
#from django.db import connection



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
        gender = request.POST['gender']
       
        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        #check for errorneous input
        if(not username.isalnum()):
            messages.error(request, 'Username should only contain letters and numbers!')
            return redirect('/signup')

        cmnd = """
        SELECT COUNT(*)
        FROM USERACCOUNT
        WHERE USER_NAME = :username
        """
        c = connection.cursor()
        c.execute(cmnd, [username]) 

        row = c.fetchone() 
        isAlreadyExist = row[0] #timeline user

        if(isAlreadyExist):
            messages.error(request,  "This Username is already taken!")
            return redirect('/signup')    

        if(password != password2):
            messages.error(request, "Passwords didn't matched")
            return redirect('/signup')     
        
        #Create the  user in database   
        cmnd = """
        SELECT NVL(MAX(USER_ID),0) 
        FROM USERACCOUNT
        """
        c = connection.cursor()
        c.execute(cmnd)      
        row = c.fetchone() 
        userid = row[0] + 1

        cmnd ="""
        INSERT INTO USERACCOUNT (USER_ID,  USER_NAME,FULL_NAME,EMAIL,PASSWORD,GENDER, DATE_OF_BIRTH, IMG_SRC)
        VALUES(:userid , :username, :fullname, :email, :password,:gender,  to_date(:birthday, 'yyyy-mm-dd'), :img_src) 
        """
        c = connection.cursor()
        img_src = "/static/user.png"
        c.execute(cmnd, [userid, username,fullname, email, password, gender, birthdate, img_src] )
        connection.commit()
        connection.close()
        
        myuser = User.objects.create_user(username=username, password=password)
        myuser.save()
        request.user = myuser
        messages.success(request, 'Your Account Has  successfully been created!')
        messages.success(request, "Login to see what other's are doing !")
        
            
        return redirect('/')

    else :
        return HttpResponse('404 - Not Found')



def handleLogin(request):
    if(request.method=='POST'):
        loginUsername=request.POST['loginUsername']
        loginPassword=request.POST['loginPassword']


        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        #validate the login user from database
        cmnd = """
        SELECT COUNT(*)
        FROM USERACCOUNT U
        WHERE U.USER_NAME = :username AND U.PASSWORD = :pass
        """
        c = connection.cursor()
        c.execute(cmnd, [loginUsername,  loginPassword])      
        row = c.fetchone() 
        isValid = row[0]

        if(isValid==0):
            messages.error(request, 'Invalid User!')
            return redirect('/')

        user = authenticate(username = loginUsername, password=loginPassword)

        if(user is not None):
            login(request, user)
            messages.success(request, "Successfully Logged In!")
            
        return redirect('/home')
        
            
    else :
        return HttpResponse('404 - Not Found')

def handleLogout(request):
    messages.success(request, "Successfully logged out!")
    logout(request)
    return redirect('/')