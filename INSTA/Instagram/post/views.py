from django.shortcuts import render

# Create your views here.
import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
import dateutil.parser

#from django.db import connection

# Create your views here.


def showPost(request, slug): 

    postid = slug

    # fetching that particular post to show
    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    	SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, P.CREATED,P.POST_ID, U.USER_ID
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
        "time": dateutil.parser.parse(str(row[3])),
        "postid": row[4],
        "userid": row[5]
    }

    username = request.user.username
    cmnd = """
    SELECT USER_ID, IMG_SRC
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone() 
    likerid = row[0]  # to check if the user alreday has liked the particular post
    img_src = row[1]


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


    #fetching the liker users' informations
    cmnd = """
    SELECT U.USER_ID, U.USER_NAME, U.IMG_SRC
    FROM USER_LIKES_POST ULP, USERACCOUNT  U
    WHERE ULP.USER_ID = U.USER_ID AND POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid]) 

    likes_count = 0
    likers = []
    for row in c:
        likerdict = {
            "liker_id": row[0],
            "liker_name": row[1],
            "img_src" : row[2],
        }
        if(not(row[1] == username)):
            likers.append(likerdict)
        likes_count += 1

    data['likes_count'] = likes_count
    data['likers'] = likers


    total_comments=0
    #fetching the comments
    cmnd = """
    SELECT U.USER_NAME , U.IMG_SRC, C.COMMENT_ID, C.CONTENT , C.CREATED "TIME" 
    FROM USER_POST_COMMENT UPC, COMMENTS C, USERACCOUNT U, REPLY R
    WHERE  UPC.COMMENT_ID = C.COMMENT_ID AND UPC.COMMENTER_ID = U.USER_ID
    AND C.COMMENT_ID = R.REPLY_ID  AND  POST_ID = :postid  AND R.REPLY_ID = R.PARENT_ID 
    """
    c = connection.cursor()
    c.execute(cmnd, [postid]) 

    comments = []
    
    for row in c:
        commentdict = {
            "commenter_name": row[0],
            "commenter_img": row[1],
            "comment_id" : row[2],
            "content": row[3], 
            "time": dateutil.parser.parse(str(row[4]))
        }
        
        comments.append(commentdict)
        total_comments += 1

    data['comments'] = comments

    #fetching the replies
    cmnd = """
    SELECT U.USER_NAME , U.IMG_SRC, C.COMMENT_ID, C.CONTENT , C.CREATED "TIME" , R.PARENT_ID
    FROM USER_POST_COMMENT UPC, COMMENTS C, USERACCOUNT U, REPLY R
    WHERE  UPC.COMMENT_ID = C.COMMENT_ID AND UPC.COMMENTER_ID = U.USER_ID
    AND C.COMMENT_ID = R.REPLY_ID  AND  POST_ID = :postid  AND R.REPLY_ID <> R.PARENT_ID
    """
    c = connection.cursor()
    c.execute(cmnd, [postid]) 

    replies = []
    for row in c:
        replydict = {
            "commenter_name": row[0],
            "commenter_img": row[1],
            "comment_id" : row[2],
            "content": row[3], 
            'time' : dateutil.parser.parse(str(row[4])),
            "parent_id" : row[5]
        }

        replies.append(replydict)
        total_comments += 1

    data['replies'] = replies
    data['comments_count'] = total_comments


    data["request_userid"] = userid
    data["request_username"] = username 
    data["request_img_src"] = img_src


    connection.close()
    return render(request, 'post/postpage.html',  data)


def likepost(request):

    postid = request.GET.get("postid","") #fetching the postid where like button was clicked
    username = request.user.username


    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)


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
    SELECT USER_ID, IMG_SRC
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username]) 

    row = c.fetchone() #fetching the userID
    userid = row[0] #liker_id
    img_src = row[1]

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

        #insert into notification table
        cmnd = """
        INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT, RELATED_POST_ID)  
        VALUES(:user_id, :poster_id, :type , :post_id)
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, poster_id,"like", postid]) 
        connection.commit()

    else : #if already liked then dislike 
        cmnd = """
        DELETE FROM USER_LIKES_POST
	    WHERE USER_ID = :userid AND POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, postid])
        connection.commit()


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
    likes_count = row[0] #count how many likes for the post 
    
    resp = {
        #handles the color changing for heart icon and number of likes shown!
        "likes_count" : likes_count,
        "liked" : liked,

        #just used only for showing the liking list dynamically
        "request_userid" : userid,
        "request_username" : username, 
        "request_img_src" : img_src,
    }
    response = json.dumps(resp)
    
    connection.close()
    return HttpResponse(response, content_type = "application/json")


def postComment(request, slug):
    if(request.method == 'POST'):
        comment = request.POST.get('comment')

        dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
        connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

        #Get the commenter id 
        username = request.user.username
        cmnd = """
        SELECT USER_ID
        FROM USERACCOUNT
        WHERE USER_NAME= :username
        """
        c = connection.cursor()
        c.execute(cmnd, [username])
        row = c.fetchone()
        commenter_id = row[0]

        cmnd = """
        SELECT NVL(MAX(COMMENT_ID),0) 
        FROM COMMENTS
        """
        c = connection.cursor()
        c.execute(cmnd)      
        row = c.fetchone() 
        commentid = row[0] + 1 #create primary key for the comment

        #INSERT THE COMMENT INTO DATABASE
        cmnd = """
        INSERT INTO COMMENTS(COMMENT_ID, CONTENT)
        VALUES(:commentid, :content) 
        """
        c = connection.cursor()
        c.execute(cmnd, [commentid, comment])
        connection.commit()

        
        postid = slug

        cmnd = """
        INSERT INTO USER_POST_COMMENT(COMMENTER_ID, POST_ID, COMMENT_ID)
        VALUES(:commenter_id, :post_id, :comment_id) 
        """
        c = connection.cursor()
        c.execute(cmnd, [commenter_id, postid,  commentid])
        connection.commit()

        #check if the comment is a reply of another comment or main comment itself
        parent_comment_id = request.POST.get('parentid')
        if(parent_comment_id == ""):
            parent_comment_id = commentid
        
        cmnd = """
        INSERT INTO REPLY(REPLY_ID, PARENT_ID)
        VALUES(:reply_id, :parent_id) 
        """
        c = connection.cursor()
        c.execute(cmnd, [commentid, parent_comment_id])
        connection.commit()


        connection.close()
        return redirect(f"/post/{slug}")
    else :
        return HttpResponse('404-Not found')