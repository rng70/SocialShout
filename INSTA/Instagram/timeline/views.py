from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from timeline.models import PostImage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import cx_Oracle
import json
import dateutil.parser


#from django.db import connection

# Create your views here.

def home(request):
    # fetching posts to show on user's timeline
    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')    
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    username = request.user.username
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone()
    likerid = row[0]  #timeline user

    cmnd = """
    SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, P.CREATED, P.POST_ID, U.USER_ID
    FROM USERACCOUNT U,  POST P
    WHERE U.USER_ID = P.USER_ID 
    AND (P.USER_ID = :userid  OR P.USER_ID IN (SELECT FOLLOWEE_ID FROM FOLLOWS WHERE FOLLOWER_ID = :userid))
    ORDER BY P.CREATED DESC
    """

    c = connection.cursor()
    c.execute(cmnd, [likerid, likerid])

    data = []
    for row in c:
        postdict = {
            "username": row[0],  # who gave that post
            "caption": row[1],
            "img_src": row[2],
            "time": dateutil.parser.parse(str(row[3])),
            "postid": row[4],
            "userid": row[5]
        }
        data.append(postdict)

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

    #Fetching the unseen notifications
    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [likerid])
    row = c.fetchone()
    total_unseen = row[0] 

    params = {'posts': data, "total_unseen": total_unseen}

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
        SELECT USER_ID
        FROM USERACCOUNT
        WHERE USER_NAME= :username
        """
        c = connection.cursor()
        c.execute(cmnd, [username])

        row = c.fetchone()
        userid = row[0]

        cmnd = """
        SELECT NVL(MAX(POST_ID),0) 
        FROM POST
        """
        c = connection.cursor()
        c.execute(cmnd)      
        row = c.fetchone() 
        postid = row[0] + 1

        cmnd = """
        INSERT INTO POST(POST_ID, CAPTION, USER_ID)
        VALUES(:postid, :caption, :user_id) 
        """
        c = connection.cursor()
        c.execute(cmnd, [postid,caption, userid])
        connection.commit()

        
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
    FROM POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid])

    row = c.fetchone()
    poster_id = row[0]

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

        if(not(userid==poster_id)):
            #insert into notification table
            cmnd = """
            INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT, RELATED_POST_ID)  
            VALUES(:user_id, :poster_id, :type , :post_id)
            """
            c = connection.cursor()
            c.execute(cmnd, [userid, poster_id,"like", postid]) 
            connection.commit()
        
    else:  # if already liked then dislike
        cmnd = """
        DELETE FROM USER_LIKES_POST
	    WHERE USER_ID = :userid AND POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])
        connection.commit()

        if(not(userid==poster_id)):
            #delete from notification table
            cmnd = """
            DELETE FROM NOTIFICATION
            WHERE FROM_ID = :user_id AND TO_ID = :poster_id AND CONTENT = :type AND RELATED_POST_ID = :post_id 
            """
            c = connection.cursor()
            c.execute(cmnd, [userid, poster_id,"like", postid]) 
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

def search(request):

    text = request.GET.get('search', '') #to be searched

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    pattern = '%' + text.lower() + '%'
    cmnd = """
    SELECT USER_ID, USER_NAME, IMG_SRC
    FROM USERACCOUNT U
    WHERE LOWER(USER_NAME) LIKE (:pattern)
    """
    c = connection.cursor()
    c.execute(cmnd, [pattern])      
    
    result = []
    total = 0
    for row in c :
        userdict = {
            "userid": row[0],  
            "username": row[1],
            "img_src": row[2],
        }
        result.append(userdict)
        total += 1

    paginator = Paginator(result, 5) #how many search results will show in one page
    page = request.GET.get('page')

    try :
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)


    #Fetching the unseen notifications
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()  # fetching the viwer_userID
    viwer_userid = row[0]

    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [viwer_userid])
    row = c.fetchone()
    total_unseen = row[0] 

    context = {
        'users': users,
        'text' : text,
        'total' : total,
        'total_unseen':total_unseen
    }

    return render(request,  'timeline/search.html', context)
