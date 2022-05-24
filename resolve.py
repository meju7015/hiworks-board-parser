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
    postViewBody = f'{listItem["user_name"]} 님이 {listItem["start"]} ~ {listItem["end"]} 까지 {listItem["name"]}을 예약하셨습니다.'
    content = '/메일/ Hi-Works 회의실 예약 알람'
    content += '날짜 : ' + listItem["start"] + ' ~ ' + listItem["end"] + '\n'
    content += '작성자 : ' + listItem['user_name'] + '\n'
    content += postViewBody
    content = parse.quote(content)

    send = 'content=' + content

    requests.post(url=os.getenv('NATE_ON_WEB_HOOK'), data=send, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

    requests.post(url=os.getenv('NATE_ON_WEB_HOOK_DESIGN'), data=send, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

    requests.post(url=os.getenv('NATE_ON_WEB_HOOK_DESIGN2'), data=send, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

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
            'referer': 'https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board/board_list',
            'User-Agent': UserAgent().chrome,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        reqBody = {
            'category_no': 7500,
            'resource_type': 'T',
            'date': date.today().strftime('%Y-%m-%d'),
            'booking_search_name': '',
            'page': 1,
            'limit': 7
        }

        boardReq = s.post(
            url='https://booking.office.hiworks.com/stickint.onhiworks.com/booking/bookingAjax/getResourceList',
            headers=headers,
            data=reqBody
        )

        if getCache() is None:
            logger.info('no cached list data : 예약시스템')
            setCache(boardReq.content)
            exit()

        prevContent = json.loads(getCache())
        nextContent = json.loads(boardReq.content)

        for i, item in enumerate(nextContent['result']['list']):
            # 리스트의 예약 내용이 증가했으면 ?
            if 'BKCP' in item['booking_info'] and len(item['booking_info']['BKCP']) > len(prevContent['result']['list'][i]['booking_info']['BKCP']):
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
                setCache(boardReq.content)

        setCache(boardReq.content)
        exit()

