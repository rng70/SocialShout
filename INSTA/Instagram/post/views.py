from django.shortcuts import render

# Create your views here.
import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
#from django.db import connection

# Create your views here.


def showPost(request, slug): 

    postid = slug

    # fetching that particular post to show
    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    	SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, TO_CHAR(P.CREATED, 'DD-MON-YYYY'),P.POST_ID, U.USER_ID
        FROM USERACCOUNT U, USERPOST UP,  POST P
        WHERE U.USER_ID = UP.USER_ID AND UP.POST_ID=P.POST_ID AND P.POST_ID = :postid
    """

    c = connection.cursor()
    c.execute(cmnd, [postid])

    row = c.fetchone()
    data = {
        "username": row[0],  # who gave that post
        "caption": row[1],
        "img_src": row[2],
        "time": row[3],
        "postid": row[4],
        "userid": row[5]
    }

    username = request.user.username
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone() 
    likerid = row[0]  # to check if the user alreday has liked the particular post


    userid = likerid
    postid = data['postid']
    cmnd = """
    SELECT COUNT(*)
    FROM USER_LIKES_POST
    WHERE USER_ID = :userid AND POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid, postid]) 

    row = c.fetchone() 
    isliked = row[0]
    data['isliked'] = isliked #is that post already liked by the request user 

    cmnd = """
    SELECT COUNT(*)
    FROM USER_LIKES_POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid]) 

    row = c.fetchone() # fetching the number of likes counts for that post
    likes_count = row[0]
    data['likes_count'] = likes_count


    connection.close()
    params = {'post' : data}
    return render(request, 'post/postpage.html',  params)


def likepost(request):

    postid = request.GET.get("postid","") #fetching the postid where like button was clicked
    username = request.user.username


    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username]) 

    row = c.fetchone() #fetching the userID
    userid = row[0]

    if(userid==None):
        return HttpResponse('404 - Not Found')

    cmnd = """
    SELECT COUNT(*)
    FROM USER_LIKES_POST
    WHERE USER_ID = :userid AND POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid, postid]) 
    row = c.fetchone() 
    already_liked = row[0]

    liked = False 

    if(already_liked==0):  #if not liked yet , then like the post
        liked = True

        cmnd = """
        INSERT INTO USER_LIKES_POST(USER_ID, POST_ID)
        VALUES(:userid,:postid)
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid]) 
        connection.commit()
    else : #if already liked then dislike 
        cmnd = """
        DELETE FROM USER_LIKES_POST
	    WHERE USER_ID = :userid AND POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])
        connection.commit()

    cmnd = """
    SELECT COUNT(*)
    FROM USER_LIKES_POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid]) 
    row = c.fetchone() 
    likes_count = row[0] #count how many likes for the post 
    
    resp = {
        "likes_count" : likes_count,
        "liked" : liked
    }
    response = json.dumps(resp)
    
    connection.close()
    return HttpResponse(response, content_type = "application/json")


def postComment(request, slug):
    if(request.method == 'POST'):
       caption = request.POST.get('comment')
       print(caption)
       
       return redirect(f"/post/{slug}")
    else :
        return HttpResponse('404-Not found')