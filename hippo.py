#encoding:utf-8
from __future__ import unicode_literals
import sys
import os
import time
import MySQLdb
import datetime
import schedule
import time
import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(level = logging.DEBUG)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
_logger.addHandler(handler)
import re
import requests
from slackclient import SlackClient

# instantiate Slack client
#slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
slack_client = SlackClient("xoxb-479391238981-490888035714-Udel4yY4VnOcVwFsGkmoaM0k")
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

max_retries = 5

# constants
RTM_READ_DELAY = 0.5 # 1 second delay between reading from RTM

# EXAM = "good evening"
EXAMPLE = "hi"

default_response = "Hello!,I can't understand,Plesse try again.".format(EXAMPLE)
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):

    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
               return message, event["channel"],event["user"]
    return None, None,None

def parse_direct_mention(message_text):

    matches = re.search(MENTION_REGEX, message_text,re.M|re.S)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1),matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel,user):
    response = None
    # This is where you start to implement more commands!
    print command
    inventory =get_countries()
    users=get_users()
    if command.lower() in inventory:
        response = sql_select(command)
    else:
        pattern = r'\s*([^\s]+)\s+([^\s]+)\s*(.+)?'
        # pattern = r'\s*([^\s]+)\s+([^\s]+)\s*((?:.|\n)+)?'
        match = re.match(pattern, command, re.S|re.M)
        if match:
            keyword,country,context = match.groups()
            if keyword == '#add':
                if country in inventory:
                    response="Sorry,The content you entered is repeated, please enter other content."
                else:
                    response = sql_insert(country, context,user)
            # elif keyword=='update-context':
            #     response=sql_update(country,context)
            # keyword, country = re.split(r'\s+', command, 1)
            elif keyword == '#delete':
                response=sql_delete(country)


    _logger.info("handle_command() print comliete!") 
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        user=user,
        text=response or default_response
    )

def get_news():

    # 获取金山词霸每日一句，英文和翻译
    url = "http://open.iciba.com/dsapi/"
    r = requests.get(url)
    contents = r.json()['content']
    note = r.json()['note']
    translation = r.json()['translation']
    return contents, note, translation

def job():
    res = None
    news=get_news()
    res=get_time()+"\n"+news[0]+"\n"+news[1]+"\n"+"\n"+"*"+news[2]+"*"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel="DEEP3NUN7",
        text=res
    )

    # schedule.every(1).minutes.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)

# def restart_program():
#     _logger.info("restart bot!!!!!")
#     python = sys.executable
#     os.execl(python, python, * sys.argv)

#连接超时，自动重连
def _auto_reconnect(running):

    while not running:
        global max_retries
        _retries=0
        if _retries < max_retries:
            _retries += 1
            try:
                # delay for longer and longer each retry in case of extended outages
                current_delay = (_retries + (_retries - 1))*5 # fibonacci, bro
                _logger.info(
                    "Attempting reconnection %s of %s in %s seconds...",
                    _retries,
                    max_retries,
                    current_delay
                )
                time.sleep(current_delay)
                running = slack_client.rtm_connect(with_team_state=False)
            except KeyboardInterrupt:
                _logger.info("KeyboardInterrupt received.")
                break
        else:
            _logger.error("Max retries exceeded")
            break
    return running

def sql_select(command):
    db = MySQLdb.connect(host="localhost",  # your host
    user="root",  # username
    passwd="5924089",  # password
    db="slackbot",
    charset="utf8")  # name of the database
    # Create a Cursor object to execute queries.
    cur = db.cursor()
    # _logger.info("start select sql.")
    # Select data from table using SQL query.
    cur.execute("SELECT context FROM `test1` where country='%s'" %command)
    rs=cur.fetchall()
    for r in rs:
        formatted_output = os.linesep.join([s for s in r[0].split('\\n')if s])
        formatted_outpu = formatted_output.replace('BAD+92','\'')
    # _logger.info("sql_select print comliete!")
    cur.close()
    db.close()
    # _logger.info("sql close!")
    return formatted_outpu

def get_countries():
    db = MySQLdb.connect(host="localhost",  # your host
    user="root",  # username
    passwd="5924089",  # password
    db="slackbot",
    charset="utf8")  # name of the database
    # Create a Cursor object to execute queries.
    cur = db.cursor()
    cur.execute('SELECT `country` FROM `test1`')
    rs = cur.fetchall()
    cur.close()
    db.close()
    return [r[0] for r in rs] if rs else []

def get_users():
    db = MySQLdb.connect(host="localhost",  # your host
    user="root",  # username
    passwd="5924089",  # password
    db="slackbot",
    charset="utf8")  # name of the database
    # Create a Cursor object to execute queries.
    cur = db.cursor()
    cur.execute('SELECT `user` FROM `test1`')
    rs = cur.fetchall()
    cur.close()
    db.close()
    return [r[0] for r in rs] if rs else []

def sql_insert(country, context,user):

    db = MySQLdb.connect(host="localhost",  # your host
    user="root",  # username
    passwd="5924089",  # password
    db="slackbot",
    charset="utf8")  # name of the database
    # Create a Cursor object to execute queries.
    cur = db.cursor()

    try:
    # insert data from table using SQL query.
        cur.execute("insert into `test1` (`country`, `context`,`user`) values('%s','%s','%s')" %(country, context,user))
        db.commit()
        response = ":clap:Data added successfully!"
    except Exception:
        response=":confused:Database operation failed,please try again!"
        db.rollback()
    finally:
        db.close()
    return response

# def sql_update(country, context,user):
#
#     db = MySQLdb.connect(host="localhost",  # your host
#     user="root",  # username
#     passwd="5924089",  # password
#     db="slackbot",
#     charset="utf8")  # name of the database
#     # Create a Cursor object to execute queries.
#     cur = db.cursor()
#     try:
#     # update data from table using SQL query.
#         cur.execute("update `Clientanalysis` set context='%s' user='%s' where country='%s'" %(context,user,country))
#         response=":clap:Data updated successfully!"
#         db.commit()
#     except Exception:
#         response=":confused:Database operation failed,please try again!"
#         db.rollback()
#     finally:
#         db.close()
#     return response

def sql_delete(country):

    db = MySQLdb.connect(host="localhost",  # your host
    user="root",  # username
    passwd="5924089",  # password
    db="slackbot",
    charset="utf8")  # name of the database
    # Create a Cursor object to execute queries.
    cur = db.cursor()
    try:
    # update data from table using SQL query.
        cur.execute("delete from `test1` where country='%s'" %(country))
        db.commit()
        response = ":clap:Data delete successfully!"
    except Exception:
        response = ":confused:Database operation failed,please try again!"
        db.rollback()
    db.close()
    return response

def get_time():

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    a=0
    running = _auto_reconnect(slack_client.rtm_connect(with_team_state=False))
    print("Starter Bot connected and running!")
    starterbot_id = slack_client.api_call("auth.test")["user_id"]
    # schedule.every(1).minutes.do(job)
    # schedule.every().day.at("15:00").do(job)
    while running:
        schedule.run_pending()
        try:
            msg = slack_client.rtm_read()
            # print msg
            command, channel, user = parse_bot_commands(msg)
            # print user
            if command:
                # _logger.info("start Getting a message.")
                handle_command(command, channel,user)
                a=a+1
                _logger.info("第'%s'次调用bot！" %a)
            time.sleep(RTM_READ_DELAY)
        except KeyboardInterrupt:
            _logger.info("KeyboardInterrupt received.")
            running = False
        except Exception as e:
            _logger.exception(e)
            # running = _auto_reconnect(slack_client.rtm_connect(with_team_state=False))
            running = _auto_reconnect(False)
