import datetime
import json

import requests
from fake_useragent import UserAgent

from src.sender import getLogger, sendMessage, makeVacationContent
from src.config import LOGIN_INFO, SEND_LIST


def vacationAlert():
    logger = getLogger()

    with requests.Session() as http:
        login_req = http.post('https://office.hiworks.com/stickint.onhiworks.com/home/ssl_login', data=LOGIN_INFO)

        if login_req.status_code != 200:
            logger.error('hi-work login failed - confirm id/pw')
            raise Exception('로그인 정보가 일치하지 않습니다.')

        today = datetime.datetime.now()

        headers = {
            'referer': 'https://hr-work.office.hiworks.com/',
            'User-Agent': UserAgent().chrome,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        response = http.get(
            url="https://office-account-api.office.hiworks.com/v3/users?filter[with_inactivated]=Y&filter[with_deleted]=Y&fields[users]=account_id,email,hiworks_account_no,is_active,is_deleted,is_office_admin,is_registed,name",
            headers=headers
        )

        lists = json.loads(response.content)
        members = lists['data']

        response = http.get(
            url=f"https://hr-work-api.office.hiworks.com/v4/vacation-calendar?filter[year]={today.year}&filter[month]={today.month}&&page[limit]=600&page[offset]=0",
            headers=headers
        )

        vacations = []
        lists = json.loads(response.content)

        for i, item in enumerate(lists['data']):
            if today.strftime('%Y-%m-%d') == item['date']:
                member = next((m for m in members if int(m['id']) == int(item['office_user_no'])), None)
                vacation = {
                    'name': member['attributes']['name'],
                    'date': item['date'],
                    'vacation_type': item['vacation_type_title']
                }

                # 휴가 타입이 연차인 경우
                if item['type'] == 'hours':
                    vacation['vacation_type'] = f"반차({item['hours']}시간) {item['start_time']} ~ {item['end_time']})"
                    vacation['start_time'] = item['start_time']
                    vacation['end_time'] = item['end_time']

                vacations.append(vacation)

        for list in SEND_LIST:
            sendMessage(
                makeVacationContent(lists=vacations),
                url=list
            )