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
from fake_useragent import UserAgent

from src.config import HI_WORKS_CACHE, LOGIN_INFO, SEND_LIST

load_dotenv(verbose=True)

def getCompInfo():
    with open('resource/properties/members.json', 'rt', encoding='UTF8') as file:
        members = json.load(file)
    return members

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
    data = {
        "markdown": content
    }

    print(url)

    requests.post(url=url, data=json.dumps(data), headers={
        'Content-Type': 'application/json'
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
        postViewBody += f"**{list['name']}**님이 오늘**{list['vacation_type']}** 입니다.\n"

    if len(lists) < 1:
        postViewBody += "오늘 휴가자는 없습니다.\n"

    content = '### 🟢 Hi-Works 휴가 알림\n'
    content += f"날짜 : {datetime.datetime.today().strftime('%Y년 %m월 %d일')} \n"
    content += postViewBody

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
    content = '### 🟢 Hi-Works 회의실 알람\n'
    content += f"**작성자** : {item['user_name']}\n"
    content += f"**날짜** : {item['start']} ~ {item['end']}\n"
    content += postViewBody
    return content


def makeVacationEmailHtml(userInfo):
    fs = codecs.open('resource/vacation-email.html', 'r', encoding='UTF8')

    html = fs.read()
    html = html.replace('{name}', userInfo['name'])
    html = html.replace('{phone}', userInfo['phone'])
    html = html.replace('{vacation_type}', userInfo['vacation_type'])
    html = html.replace('{date}', userInfo['date'])
    html = html.replace('{email}', userInfo['email'])
    html = html.replace('{eName}', userInfo['eName'])
    html = html.replace('{teamName}', userInfo['teamName'])
    html = html.replace('{positionCode}', userInfo['positionCode'])

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
    message['Subject'] = f"[{info['name']}/Stick] {info['date']} {info['vacation_type']} 알림"
    message['To'] = os.getenv('STICK_DEV_EMAIL', 'mason.jeong@stickint.kr')

    attachContent = MIMEText(makeVacationEmailHtml(userInfo=info), 'html')
    message.attach(attachContent)

    return message


def loginWith(http):
    logger = getLogger()

    response = http.post('https://office.hiworks.com/stickint.onhiworks.com/home/ssl_login', data=LOGIN_INFO)

    if response.status_code != 200:
        logger.error('hi-work login failed - confirm id/pw')
        raise Exception('로그인 정보가 일치하지 않습니다.')

    return True


def getMembers(http):
    headers = {
        'referer': 'https://hr-work.office.hiworks.com/',
        'User-Agent': UserAgent().chrome,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    response = http.get(
        url="https://office-account-api.office.hiworks.com/v3/users?filter[with_inactivated]=Y&filter[with_deleted]=Y&fields[users]=account_id,email,hiworks_account_no,is_active,is_deleted,is_office_admin,is_registed,name",
        headers=headers
    )

    if response.status_code != 200:
        raise Exception('멤버 리스트 통신 실패')

    return json.loads(response.content)['data']


def sendList(contents):
    for url in SEND_LIST:
        if url is not None:
            sendMessage(
                contents,
                url
            )