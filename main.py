import sys
import time

import selenium.common.exceptions

from src.board import boardAlert
from src.resolve import meetingAlert
from src.sender import getCompInfo
from src.vacation import vacationAlert
from src.vacation_email import sendVacationEmail

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('실행 인자를 입력 하세요')
        exit(-1)

    command = sys.argv[1]

    if command == 'board':
        boardAlert()
    elif command == 'vacation-email':
        sendVacationEmail()
    elif command == 'vacation-alert':
        vacationAlert()
    elif command == 'meeting-alert':
        meetingAlert()
    elif command == 'test':
        compInfo = getCompInfo()['lists']

        item = {
            'office_user_no': '111790'
        }
        memberInfo = ''
        for teamInfo in compInfo:
            memberInfo = next((m for m in teamInfo['user_list'] if int(m['user_no']) == int(item['office_user_no'])), None)
            if memberInfo is not None:
                break

        print(memberInfo)
    elif command == 'ch-test':
        from selenium import webdriver

        d = webdriver.Chrome(executable_path='chromedriver')
        d.get('https://simritest.com/reaction/start')
        d.implicitly_wait(3)

        d.find_element_by_xpath('//*[@id="app"]/div/div[1]/form/section/div').click()

        for i in range(10000000000):
            w = d.find_element_by_class_name('reaction-click')
            if w:
                w.click()
    elif command == 'search-google':
        from selenium import webdriver

        if len(sys.argv) < 4:
            print('검색어와 사이트 주소를 입력해 주세요.')
            exit()

        d = webdriver.Chrome(executable_path='chromedriver')
        d.get(f'https://google.com/search?q={sys.argv[2]}&filter=0')
        d.implicitly_wait(5)

        page = 1
        while True:
            try:
                lists = d.find_elements_by_tag_name('cite')
                for key, item in enumerate(lists):
                    if sys.argv[3] in item.text:
                        print(f'{page}번 페이지의 {key+1}번째로 노출되고 있습니다.')

                d.find_element_by_xpath('//*[@id="pnnext"]').click()
                page += 1
                d.implicitly_wait(3)
                continue
            except selenium.common.exceptions.NoSuchElementException:
                print('끝까지 찾았습니다. 종료합니다.')
                exit()
