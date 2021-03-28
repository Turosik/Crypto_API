import json
from json import JSONDecodeError

from aiohttp import web

from crypto_api import db
from crypto_api.utils import api_key_check, ApiKeyException


async def handle(request):
    name = request.match_info.get('name', 'Anonymous')
    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(db.user.select())
        records = await cursor.fetchall()
        text = 'Hello, ' + name + '\n' + str(len(records))

        return web.json_response(text=text)


async def ping(request):
    pong = {'ping': 'pong'}
    return web.json_response(pong)


async def api_key_check_handler(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')

    try:
        key_check = await api_key_check(json_string, request.app['db'])
    except ApiKeyException as api_key_exception:
        return web.json_response({'api_key_error': api_key_exception.message})
    except JSONDecodeError as json_decode_error:
        return web.json_response({'api_key_error': json_decode_error.msg})
    except Exception:
        return web.json_response({'api_key_error': 'Exception'})

    return web.json_response({'api_key_check': key_check})

