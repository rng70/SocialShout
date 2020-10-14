import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from timeline.models import PostImage
#from django.db import connection

# Create your views here.


def home(request):

    # fetching posts to show on user's timeline
    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    cmnd = """
    	SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, TO_CHAR(P.CREATED, 'DD-MON-YYYY'),P.POST_ID, U.USER_ID
        FROM USERACCOUNT U, USERPOST UP,  POST P
        WHERE U.USER_ID = UP.USER_ID AND UP.POST_ID=P.POST_ID
    """

    c = connection.cursor()
    c.execute(cmnd)

    data = []
    for row in c:
        postdict = {
            "username": row[0],  # who gave that post
            "caption": row[1],
            "img_src": row[2],
            "time": row[3],
            "postid": row[4],
            "userid": row[5]
        }
        data.append(postdict)

    username = request.user.username
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone()
    likerid = row[0]  # timeline user

    for d in data:
        userid = likerid
        postid = d['postid']
        cmnd = """
        SELECT COUNT(*)
        FROM USER_LIKES_POST
        WHERE USER_ID = :userid AND POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])

        row = c.fetchone()
        isliked = row[0]
        d['isliked'] = isliked  # is that post already liked by the request user

        cmnd = """
        SELECT COUNT(*)
        FROM USER_LIKES_POST
        WHERE POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [postid])

        row = c.fetchone()  # fetching the number of counts for that post
        likes_count = row[0]
        d['likes_count'] = likes_count

    params = {'posts': data}

    connection.close()
    return render(request, 'timeline/postfeed.html', params)


def post(request):
    if(request.method == 'POST'):
        image = request.FILES['image']
        caption = request.POST.get('caption', '')

        username = request.user.username

        # Create the  POST in database
        dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
        connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

        cmnd = """
        SELECT NVL(MAX(POST_ID),0) 
        FROM POST
        """
        c = connection.cursor()
        c.execute(cmnd)      
        row = c.fetchone() 
        postid = row[0] + 1

        cmnd = """
        INSERT INTO POST(POST_ID, CAPTION)
        VALUES(:postid, :caption) 
        """
        c = connection.cursor()
        c.execute(cmnd, [postid,caption])
        connection.commit()

        # c = conn.cursor()
        # c.execute("SELECT MAX(POST_ID) from INSTA.POST")
        # postid = 0
        # for row in c:
        #     postid = row[0]
        post_obj = PostImage(postid=postid, image=image)
        post_obj.save()
        post_img_ = PostImage.objects.filter(postid=postid)
        image_path = post_img_[0].image.url 

        cmnd = """
        UPDATE POST
        SET IMG_SRC = :path
        WHERE POST_ID = :postId    
        """
        c = connection.cursor()
        c.execute(cmnd, [image_path,  postid])
        connection.commit()

        cmnd = """
        SELECT USER_ID
        FROM USERACCOUNT
        WHERE USER_NAME= :username
        """
        c = connection.cursor()
        c.execute(cmnd, [username])

        row = c.fetchone()
        userid = row[0]

        cmnd = """
        INSERT INTO USERPOST(USER_ID, POST_ID)
        VALUES(:userid,:postid)
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])
        connection.commit()
        connection.close()

        return redirect('/home')

    else:
        return HttpResponse('404 -Not Found')


def likepost(request):

    # fetching the postid where like button was clicked
    postid = request.GET.get("postid", "")
    username = request.user.username

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone()  # fetching the userID
    userid = row[0]

    if(userid == None):
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

    if(already_liked == 0):  # if not liked yet , then like the post
        liked = True

        cmnd = """
        INSERT INTO USER_LIKES_POST(USER_ID, POST_ID)
        VALUES(:userid,:postid)
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])
        connection.commit()
    else:  # if already liked then dislike
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
    likes_count = row[0]  # count how many likes for the post

    resp = {
        "likes_count": likes_count,
        "liked": liked
    }
    response = json.dumps(resp)

    connection.close()
    return HttpResponse(response, content_type="application/json")
