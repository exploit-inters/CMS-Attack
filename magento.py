# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


class Magento:
    def __init__(self):
        self.required = '/logout/'

    def parse(self, text, user, passw):
        try:
            soup = BeautifulSoup(text, features="html.parser")
            form = soup.find("input", {"name": "form_key"})['value']

            return {
                'form_key': form,
                'login[username]': user,
                'login[password]': passw,
                'dummy': ''
            }
        except:
            return

    def valid(self, status, text):
        if 'IP address has been blocked' in text or status == 403:
            return False
        elif 'login[username]' not in text:
            return False
        elif '"captcha' in text:
            return False
        else:
            return True
