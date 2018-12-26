# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


class DLE:
    def __init__(self):
        self.required = 'action=logout'

    def parse(self, text, user, passw):
        try:
            a = BeautifulSoup(text, features="html.parser")
            b = a.find('select', {'name': 'selected_language'})
            c = b.find('option', selected=True)['value']

            params = {
                'subaction': 'dologin',
                'username': user,
                'password': passw,
                'selected_language': c
            }

            return params
        except:
            return

    def valid(self, status, text):
        if 'IP address has been blocked' in text or status == 403:
            return False
        elif 'selected_language' not in text:
            return False
        elif '"captcha' in text:
            return False
        else:
            return True
