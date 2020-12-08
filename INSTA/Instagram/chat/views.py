import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib import messages
import dateutil.parser
from operator import itemgetter

# Create your views here.


def getNameAndImage(i):
    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)
    cmnd = """
    SELECT FULL_NAME, IMG_SRC
    FROM USERACCOUNT
    WHERE USER_ID=:i"""
    c = connection.cursor()
    c.execute(cmnd, [i])
    rslt = c.fetchall()

    return rslt[0], rslt[1]


def returnMsgList():
    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()  # fetching the userID
    pass_userid = row[0]
    # #################################################
    # #################################################
    # print("Printing <-- -------------------------------------------------------------- -->")
    # fetching the last msg list
    cmnd = """
    SELECT 
        UNIQUE TO_ID 
    FROM 
        CHAT 
    WHERE 
        FROM_ID=:userid"""
    c = connection.cursor()
    c.execute(cmnd, [userid])
    users = c.fetchall()
    total_conv_id = []
    for user in users:
        total_conv_id.append(user[0])
    # print("Printing ---------------------------------------------------------------- -->")

    cmnd = """
    SELECT 
        UNIQUE FROM_ID 
    FROM 
        CHAT 
    WHERE 
        TO_ID=:userid"""
    c = connection.cursor()
    c.execute(cmnd, [userid])
    users = c.fetchall()
    for user in users:
        total_conv_id.append(user[0])
    user = []
    total_msg = []
    for i in total_conv_id:
        if i not in user:
            user.append(i)

    # fetching each user last message
    # fetching data one by one
    for i in user:
        c = connection.cursor()
        cmnd = """
                SELECT * 
                FROM (
	                SELECT 
	                    C.FROM_ID, C.TO_ID, C.TEXT, C.SENT_TIME, C.IS_SEEN
                    FROM 
	                    CHAT C
                    WHERE
                        (FROM_ID = :userid AND TO_ID = :i) OR (TO_ID = :userid AND FROM_ID =:i) 
                        ORDER BY SENT_TIME DESC)
                WHERE ROWNUM = 1
                """
        c.execute(cmnd, [userid, i, userid, i])
        rslt = c.fetchall()
        total_msg.append(rslt[0])
    print("Before sort: ", total_msg)
    total_msg = sorted(total_msg, key=itemgetter(3), reverse=True)
    print("After sort", total_msg)

    dict_of_msg = []
    for row in total_msg:
        f_name, f_img_src = getNameAndImage(row[0])
        t_name, t_img_src = getNameAndImage(row[1])
        msgDict = {
            'f_name': f_name,
            'f_id': row[0],
            'f_img': f_img_src,
            't_name': t_name,
            't_id': row[1],
            't_img': t_img_src,
            'last_msg': row[2],
            'time': row[3],
        }
        if row[0] == pass_userid:
            msgDict['seen'] = 1
        else:
            msgDict['seen'] = row[4]
        dict_of_msg.append(msgDict)

    # #################################################3
    # #################################################3
    return dict_of_msg


# def showChatList(request):
#     dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
#     connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

#     cmnd = """
#     SELECT USER_ID
#     FROM USERACCOUNT
#     WHERE USER_NAME = :username
#     """
#     c = connection.cursor()
#     c.execute(cmnd, [request.user.username])
#     row = c.fetchone()  # fetching the userID
#     userid = row[0]

#     msg_sent_list = []
#     total_conv_id = []
#     print("Printing <-- -------------------------------------------------------------- -->")
#     # fetching the last msg list
#     cmnd = """
#     SELECT
#         UNIQUE TO_ID
#     FROM
#         CHAT
#     WHERE
#         FROM_ID=:userid"""
#     c = connection.cursor()
#     c.execute(cmnd, [userid])
#     users = c.fetchall()
#     for user in users:
#         total_conv_id.append(user)
#         print(user)
#     # print("Printing ---------------------------------------------------------------- -->")

#     cmnd = """
#     SELECT
#         UNIQUE FROM_ID
#     FROM
#         CHAT
#     WHERE
#         TO_ID=:userid"""
#     c = connection.cursor()
#     c.execute(cmnd, [userid])
#     users = c.fetchall()
#     for user in users:
#         total_conv_id.append(user)
#         print(user)
#     user = list(set(user))
#     # fetching each user last message
#     # fetching data one by one
#     for i in user:
#         c = connection.cursor()
#         cmnd = """
#                 SELECT *
#                 FROM (
# 	                SELECT
# 	                    C.FROM_ID, C.TO_ID, C.TEXT, C.SENT_TIME
#                     FROM
# 	                    CHAT C
#                     WHERE
#                         (FROM_ID = :userid AND TO_ID = i) OR (TO_ID = userid AND FROM_ID =i)
#                         ORDER BY SENT_TIME DESC)
#                 WHERE ROWnUM = 1;
#                 """
#         c.execute(cmnd, [userid, i, userid, i])

#     return render(request, 'chat/chatlist.html', params)

def showChatList(request):
    dict_of_msg = returnMsgList()

    return render(request, 'chat/chatlist.html', dict_of_msg)


def showChat(request, to_id):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()  # fetching the userID
    userid = row[0]

    # fetching the messages
    cmnd = """
    SELECT C.FROM_ID, C.TO_ID, C.TEXT, C.SENT_TIME
    FROM CHAT C
    WHERE  
    (FROM_ID = :from_id AND TO_ID = :to_id) OR (TO_ID = :from_id AND FROM_ID =:to_id)
    ORDER BY SENT_TIME ASC
    """
    c = connection.cursor()
    c.execute(cmnd, [userid, to_id, userid,  to_id])

    chats = []
    cnt = 0
    for row in c:
        cnt += 1
        msgDict = {
            'text': row[2],
            'time': row[3],
        }
        if(row[1] == userid):
            msgDict['type'] = 'incoming'
        else:
            msgDict['type'] = 'outgoing'
        chats.append(msgDict)

    cmnd = """
    SELECT IMG_SRC
    FROM USERACCOUNT
    WHERE USER_ID = :USER_ID
    """
    c = connection.cursor()
    c.execute(cmnd, [to_id])
    row = c.fetchone()
    to_img_src = row[0]

    #fetching unseen notificatios count
    cmnd = """
    SELECT GET_UNSEEN_NOTIFICATIONS(USER_ID)
    FROM USERACCOUNT U
    WHERE U.USER_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    total_unseen = row[0]

    params = {
        'to_id': to_id,
        'chats': chats,
        'to_img_src': to_img_src,
        'total_unseen' : total_unseen,
    }
    return render(request, 'chat/chat.html', params)


def send(request, to_id):

    if(request.method == 'POST'):
        msg = request.POST['msg']

        dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
        connection = cx_Oracle.connect(
            user='insta', password='insta', dsn=dsn_tns)

        # fetching the userid
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
        INSERT INTO CHAT(FROM_ID,TO_ID, TEXT)
        VALUES (:from_id, :to_id, :text)
        """
        c = connection.cursor()
        c.execute(cmnd, [userid, to_id, msg])
        connection.commit()

        return redirect(f"/chat/{to_id}")

    else:
        return HttpResponse('404 - Not Found')
