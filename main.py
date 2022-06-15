import sys

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
