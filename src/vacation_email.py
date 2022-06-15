import os

from fake_useragent import UserAgent
from datetime import date
import requests
import json

from dotenv import load_dotenv

import datetime
from src.config import LOGIN_INFO, USER_EMAIL, USER_PHONE
from src.sender import getLogger, sendEmail, makeVacationMail, loginWith, getMembers, getCompInfo

from bs4 import BeautifulSoup as bs
import re


load_dotenv(verbose=True)

def sendVacationEmail():
    logger = getLogger()

    with requests.Session() as http:
        loginWith(http)
        today = datetime.datetime.now()
        members = getMembers(http)

        response = http.get(
            url=f"https://hr-work-api.office.hiworks.com/v4/vacation-calendar?filter[year]={today.year}&filter[month]={today.month}&&page[limit]=600&page[offset]=0",
            headers={
                'referer': 'https://hr-work.office.hiworks.com/',
                'User-Agent': UserAgent().chrome,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            }
        )

        vacations = []
        lists = json.loads(response.content)

        for i, item in enumerate(lists['data']):
            if today.strftime('%Y-%m-%d') == item['date']:
                member = next((m for m in members if int(m['id']) == int(item['office_user_no'])), None)

                response = http.post(
                    url='https://hr.office.hiworks.com/stickint.onhiworks.com/insa/org_ajax/',
                    data={
                        'pMenu': 'org_member_info',
                        'pUserNo': item['office_user_no'],
                        'pCallback': 'OrgMember.resultOrgMemberInfo'
                    },
                    headers={
                        'referer': 'https://hr.office.hiworks.com/stickint.onhiworks.com/insa/info/member/hr_lists',
                        'User-Agent': UserAgent().chrome,
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    }
                )

                html = json.loads(response.content)['result']

                # 휴대폰 번호 찾기
                soup = bs(html, 'html.parser')
                regex = re.compile(r'010-\d{4}-\d{4}')
                content = soup.find(lambda tag: tag.name == 'span' and regex.findall(tag.text))
                phone = content.getText()
                compInfo = getCompInfo()['lists']
                memberInfo = {}

                for teamInfo in compInfo:
                    memberInfo = next((m for m in teamInfo['user_list'] if int(m['user_no']) == int(item['office_user_no'])), None)
                    if memberInfo is not None:
                        break

                vacation = {
                    'name': member['attributes']['name'],
                    'date': item['date'],
                    'vacation_type': item['vacation_type_title'],
                    'email': f"{member['attributes']['account_id']}@stickint.com",
                    'phone': phone,
                    'teamName': memberInfo['node_name'],
                    'eName': memberInfo['user_name_en'],
                    'positionCode': memberInfo['position_code'],
                }

                # 휴가 타입이 연차인 경우
                if item['type'] == 'hours':
                    vacation['vacation_type'] = f"반차({item['hours']}시간) {item['start_time']} ~ {item['end_time']})"
                    vacation['start_time'] = item['start_time']
                    vacation['end_time'] = item['end_time']

                result = sendEmail(
                    from_addr=os.getenv('GMAIL_EMAIL', 'mason.jeong@stickint.kr'),
                    to_addrs=[os.getenv('STICK_DEV_EMAIL', 'mason.jeong@stickint.kr')],
                    content=makeVacationMail(info=vacation)
                )

                print(f"메일 전송 결과 : {result}")
                logger.info(f"메일 전송 결과 : {result}")

