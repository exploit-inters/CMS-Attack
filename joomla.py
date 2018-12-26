# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


class Joomla:
    def __init__(self):
        self.required = '&amp;task=logout&amp'

    def parse(self, text, user, passw):
        try:
            params = {
                'username': user,
                'passwd': passw,
                'option': 'com_login',
                'task': 'login'
            }

            a = BeautifulSoup(text, features="html.parser")

            try:
                b = a.find('fieldset', {'class': 'loginform'})
                c = b.find_all('input', {'type': 'hidden'})
            except:
                b = a.find('form', {'id': 'form-login'})
                c = b.find_all('input', {'type': 'hidden'})

            for item in c:
                if item['name'] == 'return':
                    params['return'] = item['value']

            params[c[len(c)-1]['name']] = c[len(c)-1]['value']

            try:
                c = b.find_all('select', {'name': 'lang'})[0]
                params['lang'] = ''
            except:
                pass

            return params
        except:
            return

    def valid(self, status, text):
        if 'IP address has been blocked' in text or status == 403:
            return False
        elif 'content="Joomla' not in text or status == 400:
            return False
        elif '"captcha' in text:
            return False
        else:
            return True
