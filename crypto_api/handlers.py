import json

from aiohttp import web

from crypto_api import db
from crypto_api.db import user


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


async def api_key_check(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    post_data = json.loads(json_string)
    print(post_data)
    print(dir(post_data))
    for key in post_data.keys():
        print(key)
    print(post_data['api_key'])
    async with request.app['db'].acquire() as conn:
        # result = await conn.execute(db.user.select().where(user.columns.api_key == post_data['api_key']))
        if (post_data['api_key'] == 'ytJutPoxZXuJFEdvZKsmtzYzCcXRugyFZJKOmGOjdIywBzOVYGMOrDVuNznbuxWk'):
            print('ok')
        result = await conn.execute(db.user.select().where(user.c.api_key == 'ytJutPoxZXuJFEdvZKsmtzYzCcXRugyFZJKOmGOjdIywBzOVYGMOrDVuNznbuxWk'))
        found_key = await result.first()
        print(found_key)
        if found_key:
            return web.json_response({'key': 'correct'})
        else:
            return web.json_response({'key': 'invalid'})

