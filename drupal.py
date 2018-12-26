# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


class Drupal:
    def __init__(self):
        self.required = 'Log out'

    def parse(self, text, user, passw):
        try:
            a = BeautifulSoup(text, features="html.parser")
            b = a.find('input', {'name': 'form_build_id'})['value']
            c = a.find('input', {'name': 'form_id'})['value']
            d = a.find('input', {'name': 'op'})['value']

            params = {
                'name': user,
                'pass': passw,
                'form_build_id': b,
                'form_id': c,
                'op': d
            }

            return params
        except:
            return

    def valid(self, status, text):
        if 'IP address has been blocked' in text or status == 403:
            return False
        elif 'form_build_id' not in text:
            return False
        elif '"captcha' in text:
            return False
        else:
            return True
