import cx_Oracle
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from timeline.models import PostImage

# Create your views here.

def home(request):

    #fetching posts to show on user's timeline
    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    conn = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    cmnd = """
    SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, TO_CHAR(P.CREATED, 'DD-MON-YYYY')
    FROM USERACCOUNT U, USERPOST UP,  POST P
    WHERE U.USER_ID = UP.USER_ID AND UP.POST_ID=P.POST_ID
    """

    c = conn.cursor()
    c.execute(cmnd)

    data = []
    for row in c:
        postdict = {
        "username": row[0],
        "caption": row[1],
        "img_src": row[2], 
        "time" : row[3]
        }
        data.append(postdict)
    params = {'posts' : data}

    return render(request, 'timeline/postfeed.html', params)

def post(request):
    if(request.method=='POST'):
        image = request.FILES['image']
        caption = request.POST.get('caption', '')

        username = request.user.username

        #Create the  POST in database
        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        conn = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)
       
        cmnd ="""
        INSERT INTO POST(CAPTION)
        VALUES(:caption) 
        """
        c = conn.cursor()
        c.execute(cmnd, [caption]) 
        conn.commit()

        c = conn.cursor()
        c.execute("SELECT MAX(POST_ID) from INSTA.POST")
        postid = 0
        for row in c : 
            postid = row[0]      
        post_obj = PostImage(postid=postid, image = image)
        post_obj.save()
        post_img_ = PostImage.objects.filter(postid=postid)
        image_path = post_img_[0].image.url + '\n'

       
        cmnd = """
        UPDATE POST
        SET IMG_SRC = :path
        WHERE POST_ID = :postId    
        """
        c = conn.cursor()
        c.execute(cmnd, [image_path,  postid])
        conn.commit()


        cmnd = """
        SELECT USER_ID
        FROM USERACCOUNT
        WHERE USER_NAME= :username
        """
        c = conn.cursor()
        c.execute(cmnd, [username]) 

        row = c.fetchone()
        userid = row[0]

        cmnd = """
        INSERT INTO USERPOST(USER_ID, POST_ID)
        VALUES(:userid,:postid)
        """
        c = conn.cursor()
        c.execute(cmnd, [userid, postid]) 
        conn.commit()
        conn.close()

        return redirect('/home')


    else :
        return HttpResponse('404 -Not Found')