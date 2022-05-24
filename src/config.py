import os

from dotenv import load_dotenv

load_dotenv(verbose=True)

LOGIN_INFO = {
    'office_id': os.getenv('HI_WORKS_ID'),
    'office_passwd': os.getenv('HI_WORKS_PW'),
    'ssl_login': 'Y',
    'ip_security': 1
}

USER_EMAIL = {
    '정주호': 'mason.jeong@stickint.kr',
    '김유빈': 'yb.kim@stickint.kr',
    '김경식': 'ks.kim@stickint.kr',
    '송민섭': 'ms.song@stickint.kr',
    '이희재': 'hj.lee2@stickint.kr',
    '김하영': 'hy.kim@stickint.kr',
}

USER_PHONE = {
    '정주호': '010-2396-2036',
    '김유빈': '010-4008-6098',
    '김경식': '010-7364-1023',
    '송민섭': '010-3013-0303',
    '이희재': '010-8993-1280',
    '김하영': '010-6213-6178',
}

HI_WORKS_CACHE = 'util.hiworks'

SEND_LIST = [
    os.getenv('NATE_ON_WEB_HOOK', 'localhost'),
    os.getenv('NATE_ON_WEB_HOOK_DESIGN', 'localhost'),
    os.getenv('NATE_ON_WEB_HOOK_DESIGN2', 'localhost'),
]