import logging
import sys
import json
from json import JSONDecodeError
from aiohttp import web

from crypto_api.db import save_new_address, RecordNotFound
from crypto_api.ethereum import create_new_address, get_balance, send_transaction, get_transaction_status
from crypto_api.utils import api_key_check, address_owner_check, get_value_from_post_data, CryptoApiException


async def ping(request):
    pong = {'ping': 'pong'}
    return web.json_response(pong)


# root handler, it will send control to necessary function if a correct method was specified in request
async def handle(request):
    logger = logging.getLogger(__package__)
    raw_data = await request.read()
    json_string = ''
    try:
        json_string = raw_data.decode('utf-8')
        post_data = json.loads(json_string)

        if 'method' not in post_data:
            raise CryptoApiException(handle.__name__, 'Parameter method not found in POST data')

        if not post_data['method']:
            raise CryptoApiException(handle.__name__, 'Parameter method is empty')

        # find proper function in that module by method name and call it if it is callable
        method_handle_function = getattr(sys.modules[__name__], 'api_' + post_data['method'].lower(), 'api_unknown')
        if callable(method_handle_function):
            result = await method_handle_function(request, post_data)
            logger.info('API call, method {}, response {}'.format(post_data['method'].lower(), result.text))
            return result
        else:
            logger.error('Unknown method {}'.format(post_data['method']))
            return web.json_response({'API_error': 'Unknown method {}'.format(post_data['method'])})

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
    except UnicodeDecodeError as exception:
        logger.error('UnicodeDecodeError: {}'.format(exception))
        return web.json_response({'API_error': 'Can not decode POST data'})
    except JSONDecodeError:
        logger.error('JSON decode error: {}'.format(json_string))
        return web.json_response({'API_error': 'JSON decode error'})
    except TypeError as exception:
        logger.error('TypeError: {}'.format(exception))
        return web.json_response({'API_error': 'Unsupported argument type'})


# handler for create_address method
async def api_create_address(request, post_data):
    try:
        key_check, user_id = await api_key_check(post_data, request.app['db'])

        password = await get_value_from_post_data(post_data, 'password')

        new_address, private_key = await create_new_address(password)

        response = await save_new_address(new_address, private_key, user_id, request.app['db'])

        return response

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
    except RecordNotFound:
        return web.json_response({'API_error': 'Internal server error'})


# handler for get_balance method
async def api_get_balance(request, post_data):
    try:
        key_check, user_id = await api_key_check(post_data, request.app['db'])

        owner_check, address, _ = await address_owner_check(user_id, post_data, request.app['db'], 'address')

        response = await get_balance(address)

        return response

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})


# handler for send_transaction method
async def api_send_transaction(request, post_data):
    try:
        key_check, user_id = await api_key_check(post_data, request.app['db'])

        owner_check, address_from, address_id = await address_owner_check(user_id, post_data,
                                                                          request.app['db'], 'address_from')

        address_to = await get_value_from_post_data(post_data, 'address_to')

        amount = await get_value_from_post_data(post_data, 'amount')

        response = await send_transaction(address_from, address_to, amount, request.app['db'])

        return response

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
    except RecordNotFound:
        return web.json_response({'API_error': 'Internal server error'})


# handler for get_transaction_status method
async def api_get_transaction_status(request, post_data):
    try:
        key_check, _ = await api_key_check(post_data, request.app['db'])

        transaction_hash = await get_value_from_post_data(post_data, 'transaction_hash')

        response = await get_transaction_status(transaction_hash)

        return response

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
