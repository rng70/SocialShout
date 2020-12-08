from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
import dateutil.parser
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import cx_Oracle
import json
# Create your views here.


def showNotifications(request):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    # Get the user id
    username = request.user.username
    cmnd = """
    SELECT USER_ID
    FROM USERACCOUNT
    WHERE USER_NAME= :username
    """
    c = connection.cursor()
    c.execute(cmnd, [username])
    row = c.fetchone()
    user_id = row[0]

    cmnd = """
    SELECT N.FROM_ID, U.USER_NAME, N.CONTENT, N.NOTIFIED_TIME, N.IS_SEEN, U.IMG_SRC, N.NOTIFICATION_ID, N.RELATED_POST_ID
    FROM NOTIFICATION N, USERACCOUNT U
    WHERE N.FROM_ID = U.USER_ID AND  TO_ID = :user_id
    ORDER BY N.NOTIFIED_TIME DESC
    """
    c = connection.cursor()
    c.execute(cmnd, [user_id])

    notifications = []
    total_unseen = 0
    for row in c:
        notify_dict = {
            "from_userid": row[0],
            "from_username": row[1],
            "content": row[2],
            "time": dateutil.parser.parse(str(row[3])),
            "is_seen": row[4],
            "img_src": row[5],
            "notification_id": row[6],
            "post_id": row[7],
        }

        notifications.append(notify_dict)
        if(row[4] == 0):
            total_unseen += 1

    for d in notifications:
        if(d['content'] == 'comment'):
            cmnd = """
            SELECT USER_NAME 
            FROM POST P, USERACCOUNT U
            WHERE P.USER_ID = U.USER_ID 
            AND POST_ID = :post_id
            """
            c = connection.cursor()
            c.execute(cmnd, [d['post_id']])
            row = c.fetchone()
            d['post_username'] = row[0]

    return render(request, 'notifications/notifications.html',
                  {
                      'notifications': notifications,
                      'total_unseen': total_unseen
                  })


def checkNoification(request, notification_id):

    dsn_tns = cx_Oracle.makedsn('localhost', '1521', service_name='ORCL')
    connection = cx_Oracle.connect(user='insta', password='insta', dsn=dsn_tns)

    # if click , make the notification seen by the user
    cmnd = """
    UPDATE NOTIFICATION N
    SET N.IS_SEEN = :value
    WHERE N.NOTIFICATION_ID = :id
    """
    c = connection.cursor()
    c.execute(cmnd, [1, notification_id])
    connection.commit()

    cmnd = """
    SELECT N.RELATED_POST_ID, N.FROM_ID, N.CONTENT
    FROM NOTIFICATION N
    WHERE N.NOTIFICATION_ID = :notification_id
    """
    c = connection.cursor()
    c.execute(cmnd, [notification_id])
    row = c.fetchone()

    post_id = row[0]
    from_id = row[1]
    content = row[2]

    if(content == 'like'):
        return redirect(f"/post/{post_id}")
    elif(content == "follow"):
        return redirect(f"/userprofile/{from_id}")
    else:
        return redirect(f"/post/{post_id}")
