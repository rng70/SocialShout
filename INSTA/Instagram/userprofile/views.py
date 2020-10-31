from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import cx_Oracle
import json

# Create your views here.


#showing the users profile
def showProfile(request, userid):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    #who is visiting the profile
    viewer_username = request.user.username

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [viewer_username])
    row = c.fetchone()  # fetching the viwer_userID
    viwer_userid = row[0]

    #fetching the user's profie data
    cmnd = """
    SELECT U.USER_ID, U.USER_NAME, U.FULL_NAME, U.ADDRESS, U.IMG_SRC, U.CREATED,  U.DATE_OF_BIRTH, U.BIO
    FROM USERACCOUNT U
    WHERE U.USER_ID = :user_id
    """

    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    profiledict = {
        "userid" : row[0],
        "username" : row[1],
        "fullname" : row[2],
        "address" : row[3],
        "img_src" : row[4],
        "created" : row[5],
        "birthdate" : row[6],
        "bio" : row[7],
    }

    #check if the viewer is already following that user
    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS F
    WHERE F.FOLLOWEE_ID =  :to_follow_id AND F.FOLLOWER_ID = :main_userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid, viwer_userid])
    row = c.fetchone()
    is_following = row[0]
    profiledict["is_following"] = is_following

    #fetching how many people follow this user
    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS
    WHERE FOLLOWEE_ID = :followee_id
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    followers = row[0] 
    profiledict["followers"] = followers

    #fetching how many people are followed by this people
    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS
    WHERE FOLLOWER_ID = :follower_id
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    followings = row[0] 
    profiledict["followings"] = followings

   

    return render(request, 'userprofile/profile.html', profiledict)


def showProfileByName(request, username):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])

    row = c.fetchone()  # fetching the main_userID
    userid = row[0]

    if(userid ==  None):
        return HttpResponse('404 - Not Found')

    return redirect(f"/userprofile/{userid}")

def follow(request, userid):

    main_username = request.user.username
    to_follow_id = userid

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [main_username])

    row = c.fetchone()  # fetching the main_userID
    main_userid = row[0]

    if(main_userid == None):
        return HttpResponse('404 - Not Found')

    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS F
    WHERE F.FOLLOWEE_ID =  :to_follow_id AND F.FOLLOWER_ID = :main_userid
    """
    c = connection.cursor()
    c.execute(cmnd, [to_follow_id,  main_userid])
    row = c.fetchone()
    already_followed = row[0]

    is_following = False

    if(already_followed == 0):  # if not followed yet , then follow the user
        is_following = True

        cmnd = """
        INSERT INTO FOLLOWS(FOLLOWEE_ID, FOLLOWER_ID)
        VALUES(:to_follow_id,:main_userid)
        """
        c = connection.cursor()
        c.execute(cmnd, [to_follow_id,  main_userid])
        connection.commit()

    else:  # if already followed then unfollow
        cmnd = """
        DELETE FROM FOLLOWS
	    WHERE FOLLOWEE_ID = :to_follow_id AND FOLLOWER_ID = :main_userid
        """
        c = connection.cursor()
        c.execute(cmnd, [to_follow_id, main_userid])
        connection.commit()

    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS
    WHERE FOLLOWEE_ID = :followee_id
    """
    c = connection.cursor()
    c.execute(cmnd, [to_follow_id])
    row = c.fetchone()
    followers_count = row[0]  # count how many people follows the user

    resp = {
        "followers_count": followers_count,
        "is_following": is_following
    }
    response = json.dumps(resp)

    connection.close()
    return HttpResponse(response, content_type="application/json")
