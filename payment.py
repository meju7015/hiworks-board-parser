from fake_useragent import UserAgent
from datetime import date
import requests
import json
import os

from dotenv import load_dotenv

import datetime

from src.config import LOGIN_INFO, SEND_LIST
from src.sender import getLogger, sendMessage, setCache, makeVacationContent

load_dotenv(verbose=True)


if __name__ == '__main__':
    logger = getLogger()

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

        today = datetime.datetime.today().strftime('%Y-%m-%d')

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

        for list in SEND_LIST:
            sendMessage(
                makeVacationContent(lists=vacations),
                url=list
            )