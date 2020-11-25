from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from userprofile.models import ProfileImage
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

    #fetching count of follow, following & no. of posts
    cmnd = """
    SELECT NO_OF_FOLLOWERS(:USER_ID), NO_OF_FOLLOWINGS(:USER_ID), NO_OF_POSTS(:USER_ID)
    FROM USERACCOUNT
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    followers = row[0] 
    profiledict["followers"] = followers
    followings = row[1] 
    profiledict["followings"] = followings
    total_posts = row[2]
    profiledict['total_posts'] = total_posts

    #fetching the posts
    cmnd = """
    SELECT P.POST_ID , P.IMG_SRC
    FROM POST P
    WHERE P.USER_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid]) 

    posts = []
    for row in c:
        postdict = {
            "postid": row[0],
            "img_src": row[1],
        }
        posts.append(postdict)

    posts = [posts[i:i+3] for i in range(0, len(posts), 3)] #slicing post--> 3 posts in each row
    profiledict['posts'] = posts

    #fetching the tagged posts
    cmnd = """
    SELECT P.POST_ID , P.IMG_SRC
    FROM POST P, TAGGED T
    WHERE T.POST_ID = P.POST_ID AND  T.TAGGED_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid]) 

    tagged_posts = []
    for row in c:
        taggeddict = {
            "postid": row[0],
            "img_src": row[1],
        }
        tagged_posts.append(taggeddict)

    tagged_posts = [tagged_posts[i:i+3] for i in range(0, len(tagged_posts), 3)] #slicing post--> 3 posts in each row
    profiledict['tagged_posts'] = tagged_posts

    cmnd = """
    SELECT COUNT(*)
    FROM NOTIFICATION
    WHERE TO_ID = :userid AND IS_SEEN = 0
    """
    c = connection.cursor()
    c.execute(cmnd, [viwer_userid])
    row = c.fetchone()
    total_unseen = row[0] 
    profiledict["total_unseen"] = total_unseen

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

        # #insert into notification table
        # cmnd = """
        # INSERT INTO NOTIFICATION(FROM_ID, TO_ID,CONTENT)  
        # VALUES(:user_id, :poster_id, :type)
        # """
        # c = connection.cursor()
        # c.execute(cmnd, [main_userid, to_follow_id,"follow"]) 
        # connection.commit()

    else:  # if already followed then unfollow
        cmnd = """
        DELETE FROM FOLLOWS
	    WHERE FOLLOWEE_ID = :to_follow_id AND FOLLOWER_ID = :main_userid
        """
        c = connection.cursor()
        c.execute(cmnd, [to_follow_id, main_userid])
        connection.commit()

        #delete from notification table
        # cmnd = """
        # DELETE FROM NOTIFICATION
        # WHERE FROM_ID = :from_id AND TO_ID = :to_id AND CONTENT = :type
        # """
        # c = connection.cursor()
        # c.execute(cmnd, [main_userid, to_follow_id,"follow"]) 
        # connection.commit()

    cmnd = """
    SELECT COUNT(*)
    FROM FOLLOWS
    WHERE FOLLOWEE_ID = :followee_id
    """
    c = connection.cursor()
    c.execute(cmnd, [to_follow_id])
    row = c.fetchone()
    followers_count = row[0]  # count how many people follows the user
    connection.close()
    
    resp = {
        "followers_count": followers_count,
        "is_following": is_following
    }
    response = json.dumps(resp)
    return HttpResponse(response, content_type="application/json")

def showFollowers(request, userid):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    #Fetching the followers' list
    cmnd = """
    SELECT U.USER_NAME,U.USER_ID, U.IMG_SRC
    FROM FOLLOWS F, USERACCOUNT U
    WHERE F.FOLLOWER_ID = U.USER_ID AND F.FOLLOWEE_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid]) 

    followers = []
    total_followers=0
    for row in c:
        follwerdict = {
            "username": row[0],
            "userid": row[1],
            "img_src": row[2]
        }
        followers.append(follwerdict)
        total_followers += 1

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

    data = {
        "followers" : followers,
        "total_followers" :total_followers,
        "total_unseen" : total_unseen
    }

    return render(request, 'userprofile/followers.html', data)

def showFollowings(request, userid):
    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    #Fetching the followings' list
    cmnd = """
    SELECT U.USER_NAME,U.USER_ID, U.IMG_SRC
    FROM FOLLOWS F, USERACCOUNT U
    WHERE F.FOLLOWEE_ID = U.USER_ID AND F.FOLLOWER_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid]) 

    followings = []
    total_followings=0
    for row in c:
        followingdict = {
            "username": row[0],
            "userid": row[1],
            "img_src": row[2]
        }
        followings.append(followingdict)
        total_followings += 1

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

    data = {
        "followings" : followings,
        "total_followings" :total_followings,
        "total_unseen" : total_unseen
    }

    return render(request, 'userprofile/followings.html', data)

def editProfile(request, userid):

    dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
    connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)
    
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

    #fetching the user's default information
    cmnd = """
    SELECT FULL_NAME, BIO, ADDRESS, EMAIL, TO_CHAR(DATE_OF_BIRTH, 'YYYY-MM-DD'), GENDER, PHONE_NUMBER 
    FROM USERACCOUNT
    WHERE USER_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()

    data = {
        "userid" :userid,
        "total_unseen": total_unseen,
        "fullname" : row[0],
        "bio":row[1],
        "address":row[2],
        "email":row[3],
        "birthdate":row[4],
        "gender" : row[5],
        "phone" : row[6]
    }
    return render(request, 'userprofile/editprofile.html', data)

def savePersonalInfo(request, userid):
    if(request.method == 'POST'):
        fullname= request.POST['fullname']
        bio= request.POST['bio']
        email= request.POST['email']
        phone= request.POST['phone']
        address= request.POST['address']
        birthdate = request.POST['birthdate']
        gender = request.POST['gender']

        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        cmnd ="""
        UPDATE USERACCOUNT
        SET FULL_NAME = :fullname, 
            BIO = :bio, 
            ADDRESS = :address,
			EMAIL = :email,
			Phone_Number = :phone,
			GENDER = :gender,
			DATE_OF_BIRTH = to_date(:birthday, 'yyyy-mm-dd')
        WHERE USER_ID = :userid
        """
        c = connection.cursor()
        c.execute(cmnd, [fullname, bio, address, email, phone, gender, birthdate, userid])
        connection.commit()
        connection.close()

        messages.info(request, 'Your Changes has been updated successfully!')
        return redirect(f"/userprofile/{userid}")

    else :
        return HttpResponse('404-Nor Found')


def changeProfilePic(request, userid):
    if request.method == 'POST':

        image = request.FILES['image']

        dsn_tns  = cx_Oracle.makedsn('localhost','1521',service_name='ORCL')
        connection = cx_Oracle.connect(user='insta',password='insta',dsn=dsn_tns)

        cmnd = """
        SELECT IMG_SRC 
        FROM USERACCOUNT
        WHERE USER_ID = :userid    
        """
        c = connection.cursor()
        c.execute(cmnd, [userid])
        row = c.fetchone()  # fetching the profile_image
        image_path = row[0]

        if(image_path == "/static/user.png"):
            profile_obj = ProfileImage(userid=userid,image=image)
            profile_obj.save()
        else :
            profile_obj = ProfileImage.objects.get(userid = userid)
            profile_obj.image = image
            profile_obj.save()
            
        profile_img_ = ProfileImage.objects.filter(userid=userid)
        image_path = profile_img_[0].image.url 

        cmnd = """
        UPDATE USERACCOUNT
        SET IMG_SRC = :path
        WHERE USER_ID = :userid    
        """
        c = connection.cursor()
        c.execute(cmnd, [image_path,  userid])
        connection.commit()

        messages.success(request, 'Profile Picture Updated Successfully!')
        return redirect(f"/userprofile/{userid}")

    else :
        return HttpResponse('404-Nor Found')