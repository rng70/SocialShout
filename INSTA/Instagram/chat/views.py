import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib import messages
import dateutil.parser
from operator import itemgetter


def getNameAndImage(i):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)
    cmnd = """
    SELECT USER_NAME, FULL_NAME, IMG_SRC
    FROM USERACCOUNT
    WHERE USER_ID=:i"""
    c = connection.cursor()
    c.execute(cmnd, [i])
    rslt = c.fetchall()
    rslt = rslt[0]

    return rslt[0], rslt[1], rslt[2]


def returnMsgList(request):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    # fetching the userID
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()
    pass_userid = row[0]
    userid = pass_userid

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

    # sort by time in descending order
    total_msg = sorted(total_msg, key=itemgetter(3), reverse=True)

    dict_of_msg = []
    for row in total_msg:
        name = ''
        init_msg = ''
        img_src = ''
        id = 0
        fu_name, f_name, f_img_src = getNameAndImage(row[0])
        tu_name, t_name, t_img_src = getNameAndImage(row[1])
        print("Name -->", tu_name)
        if row[0] == pass_userid:
            name = t_name
            init_msg = 'You: '
            id = row[1]
            img_src = t_img_src
        else:
            name = f_name
            init_msg = fu_name+': '
            id = row[0]
            img_src = f_img_src

        msgDict = {
            'name': name,
            'id': id,
            'img_src': img_src,
            'text': init_msg+row[2],
            'time': row[3],
        }
        if row[0] == pass_userid:
            msgDict['seen'] = 1
        else:
            msgDict['seen'] = row[4]
        dict_of_msg.append(msgDict)

    return pass_userid, dict_of_msg


def showChatList(request):

    userid, dict_of_msg = returnMsgList(request)

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT  GET_UNSEEN_NOTIFICATIONS(USER_ID), COUNT_UNSEEN_MSG(USER_ID)
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()
    total_unseen = row[0]
    total_unseen_msg = row[1]

    return render(request, 'chat/chatlist.html',
                  {
                      'userid': userid,
                      'dict_of_msg': dict_of_msg,
                      'total_unseen_msg': total_unseen_msg,
                      'total_unseen' : total_unseen,
                  })


def showChat(request, to_id):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME = :username
    """
    # fetching the userID
    c = connection.cursor()
    c.execute(cmnd, [request.user.username])
    row = c.fetchone()
    userid = row[0]

    # make the msg(s) seen
    value = 1
    cmnd = """
    UPDATE CHAT C 
    SET C.IS_SEEN = :value
    WHERE C.TO_ID = :userid AND C.FROM_ID = :to_id
    """
    c = connection.cursor()
    c.execute(cmnd, [value, userid, to_id])
    connection.commit()

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

    cmnd = """
    SELECT USER_NAME
    FROM USERACCOUNT
    WHERE USER_ID = :USER_ID
    """
    c = connection.cursor()
    c.execute(cmnd, [to_id])
    row = c.fetchone()
    to_name = row[0]

    # fetching unseen msg count
    cmnd = """
    SELECT  GET_UNSEEN_NOTIFICATIONS(USER_ID), COUNT_UNSEEN_MSG(USER_ID)
    FROM USERACCOUNT
    WHERE USER_ID = :userid
    """
    c = connection.cursor()
    c.execute(cmnd, [userid])
    row = c.fetchone()
    total_unseen = row[0]
    total_unseen_msg = row[1]

    params = {
        'to_id': to_id,
        'chats': chats,
        'to_img_src': to_img_src,
        'to_name' : to_name,
        'total_unseen_msg': total_unseen_msg,
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
