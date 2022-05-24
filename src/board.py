import json
import os

import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from src.config import SEND_LIST, LOGIN_INFO
from src.sender import getLogger, getCache, setCache, makeBoardContent, sendMessage


def boardAlert():
    logger = getLogger()

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

        prevContent = getCache('board')

        if prevContent is None:
            logger.info('no cached list data')
            setCache('board', boardReq.content)
            exit()

        prevContent = json.loads(prevContent)
        nextContent = json.loads(boardReq.content)

        print(nextContent['result']['TOTAL_CNT'])
        print(prevContent['result']['TOTAL_CNT'])

        if int(nextContent['result']['TOTAL_CNT']) > int(prevContent['result']['TOTAL_CNT']):
            newCount = int(nextContent['result']['TOTAL_CNT']) - int(prevContent['result']['TOTAL_CNT'])

            for i in range(newCount):
                post = nextContent['result']['LIST'][i]
                postViewRequest = s.get(
                    f'https://board.office.hiworks.com/stickint.onhiworks.com/bbs/board/board_view/{post["fk_board_info_no"]}/{post["no"]}/new_list')
                soup = bs(postViewRequest.text, 'html.parser')
                postViewBody = soup.find('div', {'id': 'board_content_Div'})

                try:
                    postViewBody.find('div', {'id': 'pull_div'}).decompose()
                except AttributeError:
                    pass

                if postViewBody is not None:
                    content = makeBoardContent(list=post, body=postViewBody)

                for list in SEND_LIST:
                    sendMessage(content=content, url=list)

                setCache(
                    'board',
                    json.dumps(json.loads(boardReq.content))
                )

                logger.info(f'{newCount}개의 새로운 메시지를 전송했습니다.')

        elif int(nextContent['result']['TOTAL_CNT']) < int(prevContent['result']['TOTAL_CNT']):
            setCache(
                'board',
                json.dumps(json.loads(boardReq.content))
            )

        exit()
