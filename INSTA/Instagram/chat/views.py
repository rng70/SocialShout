import cx_Oracle
import json
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib import messages
import dateutil.parser

# Create your views here.
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

    #fetching the messages
    cmnd = """
    SELECT C.FROM_ID, C.TO_ID, C.TEXT, C.SENT_TIME, U.IMG_SRC
    FROM CHAT C, USERACCOUNT U
    WHERE C.FROM_ID = U.USER_ID AND 
    (FROM_ID = :from_id AND TO_ID = :to_id) OR (TO_ID = :from_id AND FROM_ID =:to_id)
    ORDER BY SENT_TIME ASC
    """
    c = connection.cursor()
    c.execute(cmnd, [userid, to_id, userid,  to_id])
    
    chats = []
    for row in c:
        msgDict = {
            'text': row[2],
            'time': row[3],
            'img_src': row[4],
        }
        if(row[1] == userid):
            msgDict['type'] = 'incoming'
        else :
            msgDict['type'] = 'outgoing'
        chats.append(msgDict)
        print(msgDict)
    
    print(len(chats))
    params = {
        'to_id' : to_id,
        'chats' : chats
    }
    return render(request, 'chat/chat.html', params)

def send(request, to_id):

    if(request.method=='POST'):
        msg = request.POST['msg']

        dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
        connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

        #fetching the userid
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

    else :
        return HttpResponse('404 - Not Found')