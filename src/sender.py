import codecs
import datetime
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import redis

from urllib import parse

import requests

import logging
import logging.config
from dotenv import load_dotenv

from src.config import HI_WORKS_CACHE

load_dotenv(verbose=True)


def getLogger():
    with open('logging.config.json', 'rt') as file:
        config = json.load(file)

    logging.config.dictConfig(config)
    return logging.getLogger()


def getRedisClient():
    return redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=os.getenv('REDIS_PORT', 6379), decode_responses=True)


def getCache(key):
    client = getRedisClient()
    return client.get(f'{HI_WORKS_CACHE}.{key}')


def setCache(key, item):
    client = getRedisClient()
    return client.set(f'{HI_WORKS_CACHE}.{key}', item)


def merge(old, new):
    lists = []
    for i in new:
        if i not in old:
            lists.append(i)
    return lists


def sendMessage(content, url):
    requests.post(url=url, data=content, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })


def smtpClient():
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp.login(user=os.getenv('GMAIL_EMAIL'), password=os.getenv('GMAIL_PASSWORD'))
    return smtp


def sendEmail(from_addr, to_addrs, content):
    smtpClient().sendmail(
        from_addr=from_addr,
        to_addrs=to_addrs,
        msg=content.as_string()
    )

    return smtpClient().quit()


def makeVacationContent(lists):
    postViewBody = ''

    for list in lists:
        postViewBody += f"{list['name']}님이 오늘{list['vacation_type']} 입니다.\n"

    if len(lists) < 1:
        postViewBody += "오늘 휴가자는 없습니다.\n"

    content = '/자리비움/ Hi-Works 휴가 알림\n'
    content += f"날짜 : {datetime.datetime.today().strftime('%Y년 %m월 %d일')} \n"
    content += postViewBody
    content = f"content={parse.quote(content)}"

    return content


def makeBoardContent(list, body):
    postViewBody = body.text
    content = '### 🟢 Hi-Works 게시판 알람'
    content += f"**제목** : {list['title']}\n"
    content += f"**날짜** : {list['write_date']}\n"
    content += f"**작성자** : {list['name']}\n"
    content += postViewBody
    content += f"**링크** : [바로가기](https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board/board_view/{list['fk_board_info_no']}/{list['no']}/new_list)"
    return content


def makeMeetingContent(item):
    postViewBody = f"{item['user_name']} 님이 {item['start']} ~ {item['end']} 까지 {item['name']}을 예약했습니다."
    content = '/메일/ Hi-Works 회의실 알람\n'
    content += f"작성자 : {item['user_name']}\n"
    content += f"날짜 : {item['start']} ~ {item['end']}\n"
    content += postViewBody
    content = f"content={parse.quote(content)}"
    return content




def makeVacationEmailHtml(userInfo):
    fs = codecs.open('resource/vacation-email.html', 'r', encoding='UTF8')

    html = fs.read()
    html = html.replace('{name}', userInfo['name'])
    html = html.replace('{phone}', userInfo['phone'])
    html = html.replace('{vacation_type}', userInfo['vacation_type'])
    html = html.replace('{date}', userInfo['date'])
    html = html.replace('{email}', userInfo['email'])

    if 'start_time' in userInfo and 'end_time' in userInfo:
        html = html.replace(
            '{content}',
            f"금일 {userInfo['vacation_type']} 사용 으로 {userInfo['start_time']} 부터 {userInfo['end_time']} 까지 부재 입니다. <br>업무에 참고 부탁 드립니다."
        )
    else:
        html = html.replace(
            '{content}',
            f"금일 {userInfo['vacation_type']} 사용 으로 부재입니다.<br>업무에 참고 부탁 드립니다."
        )

    if 'hours' in userInfo:
        html = html.replace('{hours}', userInfo['hours'])

    if 'start_time' in userInfo and 'end_time' in userInfo:
        html = html.replace('{start_time}', userInfo['start_time'])
        html = html.replace('{end_time}', userInfo['end_time'])

    return html


def makeVacationMail(info):
    message = MIMEMultipart('alternative')
    message['Subject'] = f"[{info['name']}/STICK] {info['date']} {info['vacation_type']} 알림"
    message['To'] = os.getenv('STICK_DEV_EMAIL', 'stickdev@stickint.com')

    attachContent = MIMEText(makeVacationEmailHtml(userInfo=info), 'html')
    message.attach(attachContent)

    return message

