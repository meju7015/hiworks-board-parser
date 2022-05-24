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

from src.config import LOGIN_INFO, SEND_LIST
from src.sender import getLogger, getCache, setCache, makeMeetingContent, sendMessage

load_dotenv(verbose=True)

def meetingAlert():
    logger = getLogger()

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

        if getCache('list') is None:
            logger.info('no cached list data : 예약시스템')
            setCache('list', boardReq.content)
            exit()

        prevContent = json.loads(getCache('list'))
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
                        content = makeMeetingContent({
                            'name': item['name'],
                            'user_name': item['booking_info']['BKCP'][n]['user_name'],
                            'start': item['booking_info']['BKCP'][n]['start'],
                            'end': item['booking_info']['BKCP'][n]['end'],
                        })

                        for url in SEND_LIST:
                            sendMessage(
                                content=content,
                                url=url
                            )

            # 예약이 없는 상태에서 최초 예약이 들어올경우
            elif 'BKCP' not in prevContent['result']['list'][i]['booking_info'] and 'BKCP' in item['booking_info']:
                # 모든게 새로들어온것이다.
                for n in range(len(item['booking_info']['BKCP'])):
                    content = makeMeetingContent({
                        'name': item['name'],
                        'user_name': item['booking_info']['BKCP'][n]['user_name'],
                        'start': item['booking_info']['BKCP'][n]['start'],
                        'end': item['booking_info']['BKCP'][n]['end'],
                    })

                    for url in SEND_LIST:
                        sendMessage(
                            content=content,
                            url=url
                        )

                setCache('list', boardReq.content)
            elif 'BKCP' in item['booking_info'] \
                    and len(item['booking_info']['BKCP']) < len(prevContent['result']['list'][i]['booking_info']['BKCP']):
                setCache('list', boardReq.content)

        setCache('list', boardReq.content)

