import datetime
import hashlib

from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from datetime import date
import requests
import json
import redis
from urllib import parse
from prettyprinter import pprint

import logging
import logging.config
import os

from dotenv import load_dotenv

import datetime

load_dotenv(verbose=True)

LOGIN_INFO = {
    'office_id': os.getenv('HI_WORKS_ID'),
    'office_passwd': os.getenv('HI_WORKS_PW'),
    'ssl_login': 'Y',
    'ip_security': 1
}

def getRedisClient():
    return redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), decode_responses=True)

def getCache():
    client = getRedisClient()
    return client.get('util.hiworks.resolve.list')

def setCache(item):
    client = getRedisClient()
    return client.set('util.hiworks.resolve.list', item)

def merge(oldList, newList):
    lists = []
    for i in newList:
        if i not in oldList:
            lists.append(i)

    return lists

def sendMessage(listItem):
    postViewBody = ''
    for item in listItem:
        postViewBody += f"{item['name']}님이 오늘 {item['vacation_type']} 입니다.\n"

    content = '/자리비움/ Hi-Works 휴가 알림\n'
    content += '날짜 : ' + datetime.datetime.today().strftime('%Y년 %m월 %d일') + '\n'
    content += postViewBody
    content = parse.quote(content)

    send = 'content=' + content

    requests.post(url=os.getenv('NATE_ON_WEB_HOOK'), data=send, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

def sendEmail(listItem):
    return

def __get_logger():
    with open('logging.config.json', 'rt') as file:
        config = json.load(file)

    logging.config.dictConfig(config)
    return logging.getLogger()

if __name__ == '__main__':
    logger = __get_logger()

    with requests.Session() as s:
        loginReq = s.post('https://office.hiworks.com/stickint.onhiworks.com/home/ssl_login', data=LOGIN_INFO)

        if loginReq.status_code != 200:
            logger.error('hi-works login failed - confirm id/pw')
            raise Exception('로그인 정보가 일치하지 않습니다.')

        headers = {
            'referer': 'https://hr-work.office.hiworks.com/',
            'User-Agent': UserAgent().chrome,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        reqBody = {
            'category_no': 7500,
            'resource_type': 'T',
            'date': date.today().strftime('%Y-%m-%d'),
            'booking_search_name': '',
            'page': 1,
            'limit': 7
        }

        #today = datetime.datetime.today().strftime('%Y-%m-%d')

        today = '2022-04-08'

        boardReq = s.get(
            url=f'https://hr-work-api.office.hiworks.com/v4/user-work-data-calendar?&&filter[work_date][gte]={today}&filter[work_date][lte]={today}&page[limit]=20&page[offset]=0',
            headers=headers,
            data=reqBody
        )

        contents = json.loads(boardReq.content)

        vacations = []

        for i, item in enumerate(contents['data']):
            for userWorkData in item['user_work_data']:
                if 'vacation_data' in userWorkData:
                    for vacationData in userWorkData['vacation_data']:
                        print(vacationData)
                        vacation = {
                            'name': item['name'],
                            'date': today,
                            'vacation_type': vacationData['vacation_type_title'],
                        }

                        if 'hours' in vacationData:
                            vacation['vacation_type'] = "반차"
                            vacation['vacation_type'] += f"({vacationData['hours']}시간)"

                        if 'start_time' in vacationData and 'end_time' in vacationData:
                            vacation['vacation_type'] += f" {vacationData['start_time']} ~ {vacationData['end_time']}"


                        vacations.append(vacation)


        sendMessage(vacations)

        '''for i, item in enumerate(nextContent['result']['list']):
            # 리스트의 예약 내용이 증가했으면 ?
            if 'BKCP' in item['booking_info'] \
                    and len(item['booking_info']['BKCP']) > len(prevContent['result']['list'][i]['booking_info']['BKCP']):
                # 새로 들어온예약이 무엇인지 찾아보자
                for n in range(len(item['booking_info']['BKCP'])):
                    isContinue = False
                    # 새로운것이 이미 뿌려졌던건지 비교
                    for c2 in prevContent['result']['list'][i]['booking_info']['BKCP']:
                        if c2['no'] == item['booking_info']['BKCP'][n]['no']:
                            isContinue = True

                    if isContinue:
                        continue
                    else:
                        sendMessage({
                            'name': item['name'],
                            'user_name': item['booking_info']['BKCP'][n]['user_name'],
                            'start': item['booking_info']['BKCP'][n]['start'],
                            'end': item['booking_info']['BKCP'][n]['end'],
                        })
            # 예약이 없는 상태에서 최초 예약이 들어올경우
            elif 'BKCP' not in prevContent['result']['list'][i]['booking_info'] and 'BKCP' in item['booking_info']:
                # 모든게 새로들어온것이다.
                for n in range(len(item['booking_info']['BKCP'])):
                    sendMessage({
                        'name': item['name'],
                        'user_name': item['booking_info']['BKCP'][n]['user_name'],
                        'start': item['booking_info']['BKCP'][n]['start'],
                        'end': item['booking_info']['BKCP'][n]['end'],
                    })
                setCache(boardReq.content)
            elif 'BKCP' in item['booking_info'] \
                    and len(item['booking_info']['BKCP']) < len(prevContent['result']['list'][i]['booking_info']['BKCP']):
                setCache(boardReq.content)'''

        setCache(boardReq.content)
        exit()

