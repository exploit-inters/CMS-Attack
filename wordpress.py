# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


class WordPress:
    def __init__(self):
        self.required = 'wp-login.php?action=logout'

    def parse(self, text, user, passw):
        try:
            soup = BeautifulSoup(text, features="html.parser")
            r_to = soup.find("input", {"name": "redirect_to"})['value']
            b_nm = soup.find("input", {"name": "wp-submit"})['value']

            return {
                'log': user,
                'pwd': passw,
                'wp-submit': b_nm,
                'redirect_to': r_to,
                'testcookie': '1'
            }
        except:
            return

    def valid(self, status, text):
        if 'IP address has been blocked' in text or status == 403:
            return False
        elif 'redirect_to' not in text:
            return False
        elif '"captcha' in text:
            return False
        else:
            return True
