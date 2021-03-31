import json
import logging
from json import JSONDecodeError
import sys

from aiohttp import web

from crypto_api.db import save_new_address, RecordNotFound, save_new_transaction
from crypto_api.ethereum import create_new_address, get_balance, send_transaction, get_transaction_status
from crypto_api.utils import api_key_check, address_owner_check, get_value_from_json, CryptoApiException

logger = logging.getLogger(__package__)
log_info = 'API call, method {}, response {}'


async def ping(request):
    pong = {'ping': 'pong'}
    return web.json_response(pong)


async def handle(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    try:
        post_data = json.loads(json_string)

        if 'method' not in post_data:
            raise CryptoApiException(handle.__name__, 'Parameter method not found in POST data')

        if not post_data['method']:
            raise CryptoApiException(handle.__name__, 'Parameter method is empty')

        method_handle_function = getattr(sys.modules[__name__], 'api_' + post_data['method'], 'api_unknown')
        if callable(method_handle_function):
            # TODO now call the proper handler
            return web.json_response({'result': 'callable'})
            # reply = func(request)
        else:
            return web.json_response({'API_error': 'Unknown method {}'.format(post_data['method'])})

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
    except JSONDecodeError:
        logger.error('JSON decode error: {}'.format(json_string))
        return web.json_response({'API_error': 'JSON decode error'})
    except TypeError:
        logger.error('Unsupported argument type: {}'.format(json_string))
        return web.json_response({'API_error': 'Unsupported argument type'})


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

    logger.info(log_info.format('create-address', response.text))
    return response


async def api_get_balance(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    key_check, response, user_id = await api_key_check(json_string, request.app['db'])
    if key_check:
        owner_check, response, address, _ = await address_owner_check(user_id, json_string,
                                                                      request.app['db'], 'address')
        if owner_check:
            balance = await get_balance(address)
            response = web.json_response({'result': balance})

    return response


async def api_send_transaction(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')
    key_check, response, user_id = await api_key_check(json_string, request.app['db'])
    if not key_check:
        return response

    owner_check, response, address_from, address_id = await address_owner_check(user_id, json_string,
                                                                                request.app['db'], 'address_from')
    if not owner_check:
        return response

    address_to, response = await get_value_from_json(json_string, 'address_to')
    if not address_to:
        return response

    amount, response = await get_value_from_json(json_string, 'amount')
    if not amount:
        return response

    tx_hash, nonce, response = await send_transaction(address_from, address_to, amount, request.app['db'])
    if not tx_hash:
        return response

    response = await save_new_transaction(address_id, address_to, nonce, tx_hash, request.app['db'])

    return response


async def api_get_transaction_status(request):
    raw_data = await request.read()
    json_string = raw_data.decode('utf-8')

    key_check, response, _ = await api_key_check(json_string, request.app['db'])
    if not key_check:
        return response

    transaction_hash, response = await get_value_from_json(json_string, 'transaction_hash')
    if not transaction_hash:
        return response

    response = await get_transaction_status(transaction_hash)

    return response
