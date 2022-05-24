import sys

from src.board import boardAlert
from src.resolve import meetingAlert
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
