import json
from json import JSONDecodeError

from aiohttp import web

from crypto_api import db
from crypto_api.db import save_new_address, RecordNotFound
from crypto_api.ethereum import create_new_address, get_balance
from crypto_api.utils import api_key_check, address_owner_check, get_value_from_json


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
    _, response, _ = await api_key_check(json_string, request.app['db'])
    return response


async def api_create_address(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    key_check, response, user_id = await api_key_check(json_string, request.app['db'])
    post_data = json.loads(json_string)
    if 'password' not in post_data:
        return web.json_response({'account_creation_error': 'Password not found in POST data'})
    password = post_data['password']
    if not password:
        return web.json_response({'account_creation_error': 'Password should not be empty'})

    if key_check:
        new_address, private_key = await create_new_address(password)
        try:
            response = await save_new_address(new_address, private_key, user_id, request.app['db'])
        except RecordNotFound as exception:
            # TODO handle exceptions
            pass
    return response


async def api_get_balance(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    key_check, response, user_id = await api_key_check(json_string, request.app['db'])
    if key_check:
        owner_check, response, address = await address_owner_check(user_id, json_string,
                                                                   request.app['db'], 'address')
        if owner_check:
            balance = await get_balance(address)
            response = web.json_response({'balance': balance})

    return response


async def api_send_transaction(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    key_check, response, user_id = await api_key_check(json_string, request.app['db'])
    if not key_check:
        return response

    owner_check, response, address_from = await address_owner_check(user_id, json_string,
                                                                    request.app['db'], 'address_from')
    if not owner_check:
        return response

    address_to, response = get_value_from_json(json_string, 'address_to')
    if not address_to:
        return response

    # TODO send trx

    return response
