from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
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
    return client.get('util.hiworks.board.list')


def setCache(item):
    client = getRedisClient()
    return client.set('util.hiworks.board.list', item)


def merge(oldList, newList):
    lists = []
    for i in newList:
        if i not in oldList:
            lists.append(i)

    return lists

def __get_logger():
    with open('logging.config.json', 'rt') as file:
        config = json.load(file)

    logging.config.dictConfig(config)
    return logging.getLogger()

if __name__ == '__main__':
    logger = __get_logger()

    logger.info('hi-works parser launched')

    with requests.Session() as s:
        loginReq = s.post('https://office.hiworks.com/stickint.onhiworks.com/home/ssl_login', data=LOGIN_INFO)

        if loginReq.status_code != 200:
            logger.error('hi-works login failed - confirm id/pw')
            raise Exception('로그인 정보가 일치하지 않습니다.')

        headers = {
            'referer': 'https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board/board_list',
            'User-Agent': UserAgent().chrome
        }

        boardReq = s.get(
            url='https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board_ajax/getBoardContentsList',
            headers=headers)

        prevContent = getCache()

        if prevContent is None:
            logger.info('no cached list data')
            setCache(json.dumps(json.loads(boardReq.content)['result']['LIST']))
            exit()

        prevContent = json.loads(prevContent)
        nextContent = json.loads(boardReq.content)['result']['LIST']

        merges = merge(prevContent, nextContent)

        if merges is None:
            setCache(json.dumps(json.loads(boardReq.content)['result']['LIST']))
            exit()

        for data in merges:
            viewReq = s.get(f'https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board/board_view/{data["fk_board_info_no"]}/{data["no"]}/new_list')
            soup = bs(viewReq.text, 'html.parser')
            body = soup.find('div', {'id': 'board_content_Div'})

            try:
                body.find('div', {'id': 'pull_div'}).decompose()
            except AttributeError:
                pass

            if body is not None:
                body = body.text
                content = '/메일/ Hi-Works 게시판 알람 '
                content += '제목 : ' + data['title'] + '\n'
                content += '날짜 : ' + data['write_date'] + '\n'
                content += body
                content = parse.quote(content)

                send = 'content=' + content

                pprint(send)

                requests.post(url=os.getenv('NATE_ON_WEB_HOOK'), data=send, headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                })


    setCache(json.dumps(json.loads(boardReq.content)['result']['LIST']))
