from django.shortcuts import render

# Create your views here.
import cx_Oracle
import json
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from timeline.models import PostImage
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
    	SELECT U.USER_NAME, NVL(P.CAPTION, ' '), P.IMG_SRC, P.CREATED,P.POST_ID, U.USER_ID, U.IMG_SRC
        FROM USERACCOUNT U, POST P
        WHERE U.USER_ID = P.USER_ID  AND P.POST_ID = :postid
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
        "userid": row[5],
        "user_img_src" : row[6],
    }

    username = request.user.username
    #fetching the tagged people
    cmnd = """
    SELECT U.USER_ID, U.USER_NAME, U.IMG_SRC
    FROM TAGGED T, USERACCOUNT U, POST P
    WHERE T.TAGGED_ID = U.USER_ID AND T.POST_ID = P.POST_ID AND T.POST_ID = :postid  AND T.TAGGED_ID <> P.USER_ID
    """
    c = connection.cursor()
    c.execute(cmnd, [postid])

    tagged = []
    no_of_tags = 0
    for row in c:
        tagDict = {
            'userid' : row[0],
            'username' : row[1],
            'img_src' : row[2],
        }
        no_of_tags += 1
        if(no_of_tags == 1):
            data['firstTag'] = tagDict
        else :
            tagged.append(tagDict)
    data['tagged'] = tagged
    data['no_of_tags'] = no_of_tags

    
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
    SELECT U.USER_NAME , U.IMG_SRC, C.COMMENT_ID, C.CONTENT , C.CREATED 
    FROM  COMMENTS C, USERACCOUNT U, REPLY R
    WHERE C.COMMENTER_ID = U.USER_ID AND C.COMMENT_ID = R.REPLY_ID  
	AND  C.POST_ID = :post_id  AND R.REPLY_ID = R.PARENT_ID
	ORDER BY C.CREATED ASC
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
    SELECT U.USER_NAME , U.IMG_SRC, C.COMMENT_ID, C.CONTENT , C.CREATED , R.PARENT_ID
    FROM COMMENTS C, USERACCOUNT U, REPLY R
    WHERE C.COMMENTER_ID = U.USER_ID AND C.COMMENT_ID = R.REPLY_ID  
    AND  C.POST_ID = :postid  AND R.REPLY_ID <> R.PARENT_ID
    ORDER BY C.CREATED ASC
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

    #Fetching the unseen notifications
    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    total_unseen = row[0] 
    data["total_unseen"] = total_unseen


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

        # if(not(userid==poster_id)):
        #     #insert into notification table
        #     cmnd = """
        #     INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT, RELATED_POST_ID)  
        #     VALUES(:user_id, :poster_id, :type , :post_id)
        #     """
        #     c = connection.cursor()
        #     c.execute(cmnd, [userid, poster_id,"like", postid]) 
        #     connection.commit()

    else : #if already liked then dislike 
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
        postid = slug

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
        INSERT INTO COMMENTS(COMMENT_ID, CONTENT, COMMENTER_ID, POST_ID)
        VALUES(:commentid, :content,  :commenter_id, :post_id) 
        """
        c = connection.cursor()
        c.execute(cmnd, [commentid, comment, commenter_id, postid])
        connection.commit()

        #get the poster id      
        cmnd = """
        SELECT USER_ID
        FROM POST
        WHERE POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [postid])
        row = c.fetchone()
        poster_id = row[0]


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

        # if(not(commenter_id==poster_id)):
        #     #insert into notification table
        #     cmnd = """
        #     INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT, RELATED_POST_ID)  
        #     VALUES(:commenter_id, :poster_id, :type , :post_id)
        #     """
        #     if(parent_comment_id == commentid):
        #         content = "comment"
        #     else :
        #         content = "reply"
        #     c = connection.cursor()
        #     c.execute(cmnd, [commenter_id, poster_id,content, postid]) 
        #     connection.commit()

        connection.close()

        return redirect(f"/post/{slug}")
    else :
        return HttpResponse('404-Not found')

def editpost(request, postid):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    #fetching the caption
    cmnd = """
    SELECT CAPTION
    FROM POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid])
    row = c.fetchone()  
    caption = row[0]

    #Fetching the unseen notifications
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()  # fetching the userID
    userid = row[0]

    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    total_unseen = row[0] 

    data = { "postid" : postid, "total_unseen":total_unseen, "caption":caption}  
    return render(request, 'post/editpost.html', data)


def saveEditedPost(request, postid):
    if(request.method=='POST'):
        edited=request.POST['edited'] #fetching the edited caption

        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        #save the edited post in database
        cmnd = """
        UPDATE POST
        SET CAPTION = :edited
        WHERE POST_ID = :postid
        """
        c = connection.cursor()
        c.execute(cmnd, [edited,  postid])  
        connection.commit()    
        connection.close()

        return redirect(f"/post/{postid}")

    else :
        return HttpResponse('404 - Not Found')
    
def addtag(request,  postid): #add tag in postid
    if(request.method=='POST'):
        tagged_people = request.POST['tagged_people']
        x = set(tagged_people.split("@"))
        x.remove('')

        if(len(x) == 0):
            messages.error(request, 'You have not selected anyone!')
            return redirect(f"/post/{postid}")

        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        cmnd = """
        SELECT USER_ID
        FROM USERACCOUNT
        WHERE USER_NAME = :username
        """
        c = connection.cursor()
        c.execute(cmnd, [request.user.username])
        row = c.fetchone()  # fetching the userID or poster_id
        userid = row[0]

        for tagged_name in x :
            #add tag in database table
            cmnd = """
            INSERT INTO TAGGED(TAGGED_ID, POST_ID) 
            VALUES( (SELECT USER_ID FROM USERACCOUNT WHERE USER_NAME = :tagged_name), :postid)
            """
            c = connection.cursor()
            c.execute(cmnd, [tagged_name, postid])  
            connection.commit() 

            # if (tagged_name == request.user.username):
            #     continue  
            
            # #insert into notification table
            # cmnd = """
            # INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT, RELATED_POST_ID)  
            # VALUES(:user_id, (SELECT USER_ID FROM USERACCOUNT WHERE USER_NAME = :tagged_name), :type , :post_id)
            # """
            # c = connection.cursor()
            # c.execute(cmnd, [userid, tagged_name,"tag", postid]) 
            # connection.commit() 

        connection.close()
        return redirect(f"/post/{postid}")
    else :
        return HttpResponse('404 - Not Found')

def autocomplete(request, postid): #autocomplte searchBar while searching for users to tag in posts

    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    #https://jqueryui.com/autocomplete/
    if 'term' in request.GET:
        to_find = request.GET.get('term')
        
        cmnd = """
        SELECT U.USER_NAME
        FROM USERACCOUNT U
        WHERE LOWER(USER_NAME) LIKE ('%' ||LOWER(:term) || '%')
        AND USER_ID NOT IN (SELECT TAGGED_ID FROM TAGGED WHERE POST_ID = :postid)
        """
        c = connection.cursor()
        c.execute(cmnd, [to_find, postid]) 
        
        titles = list()
        for row in c:
            titles.append(row[0])
        
        return JsonResponse(titles, safe=False)

    #Fetching the unseen notifications
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()  # fetching the userID
    userid = row[0]

    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    total_unseen = row[0] 

    return render(request, 'post/addtag.html', {'postid':postid, 'total_unseen':total_unseen})


def deleltePost(request, postid):

    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

    #fetching the userid
    cmnd = """
    SELECT USER_ID
    FROM POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid])
    row = c.fetchone()  
    userid  = row[0]

    #deletes post
    cmnd = """
    DELETE FROM POST
    WHERE POST_ID = :postid
    """
    c = connection.cursor()
    c.execute(cmnd, [postid])
    connection.commit()

    post_= PostImage.objects.filter(postid=postid)
    post_.delete()

    messages.info(request, 'Post deleted successfully!')
    return redirect(f"/userprofile/{userid}")