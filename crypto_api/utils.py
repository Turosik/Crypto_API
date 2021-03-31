import inspect
import json
import logging
from json import JSONDecodeError

from aiohttp import web

from crypto_api import db
from crypto_api.db import user, user_crypto_address
from crypto_api.settings import config, BASE_DIR


def config_logger():
    logger = logging.getLogger(__package__)
    logger.setLevel(config['logger']['level'])
    formatter = logging.Formatter('%(asctime)-23s %(levelname)-8s %(message)s')

    # try to create file handler
    try:
        file_handler = logging.FileHandler(filename=BASE_DIR / config['logger']['file_name'], mode="a+")
        print('using log file name: {}'.format(file_handler.baseFilename))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except FileNotFoundError:
        print('can not create log file')

    # additionally create stream handler if log to stream is set True
    if config['logger']['stream']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config['logger']['level'])
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


class CryptoApiException(Exception):
    def __init__(self, caller, description):
        self.caller = caller
        self.message = description

        # use only logger for output, further behavior depends on logger settings
        logger = logging.getLogger(__package__)
        logger.error(self.__str__())

    def __str__(self):
        return 'API EXCEPTION (module {}): {}'.format(self.caller, self.message)


async def get_value_from_json(json_string, param_name):
    try:
        post_data = json.loads(json_string)

        if param_name not in post_data:
            raise CryptoApiException(inspect.stack()[1].function,
                                     'Parameter {} not found in POST data'.format(param_name))

        if not post_data[param_name]:
            raise CryptoApiException(inspect.stack()[1].function,
                                     'Parameter {} is empty'.format(param_name))

        return post_data[param_name], None

    except CryptoApiException as api_exception:
        return None, web.json_response({'API_error': api_exception.message})
    except JSONDecodeError:
        logger = logging.getLogger(__package__)
        logger.error('JSON decode error: {}'.format(json_string))
        return None, web.json_response({'API_error': 'JSON decode error'})
    except Exception:
        return None, web.json_response({'API_error': 'Internal server error'})


async def api_key_check(json_string, database):
    try:
        post_data = json.loads(json_string)

        if 'api_key' not in post_data:
            raise CryptoApiException(inspect.stack()[1].function, 'API key not found in POST data')

        async with database.acquire() as conn:
            result = await conn.execute(db.user.select().where(user.columns.api_key == post_data['api_key']))
            found_key = await result.first()

            if found_key:
                return True, web.json_response({'api_key_check': True}), found_key.id
            else:
                raise CryptoApiException(inspect.stack()[1].function, 'API key does not exist')

    except CryptoApiException as api_key_exception:
        return False, web.json_response({'api_key_error': api_key_exception.message}), None
    except JSONDecodeError as json_decode_error:
        return False, web.json_response({'api_key_error': json_decode_error.msg}), None
    except Exception:
        return False, web.json_response({'api_key_error': 'Exception'}), None


async def address_owner_check(user_id, json_string, database, param_name):
    try:
        post_data = json.loads(json_string)

        if param_name not in post_data:
            raise CryptoApiException(inspect.stack()[1].function, 'Address not found in POST data')

        async with database.acquire() as conn:
            result = await conn.execute(db.user_crypto_address.select()
                                        .where(user_crypto_address.columns.blockchain_address == post_data[param_name])
                                        .where(user_crypto_address.columns.user == user_id))
            found_address = await result.first()

            if found_address:
                return True, web.json_response({'address_owner_check': True}),\
                       found_address.blockchain_address, found_address.id
            else:
                raise CryptoApiException(inspect.stack()[1].function, 'This is not your address')

    except CryptoApiException as address_exception:
        return False, web.json_response({'address_error': address_exception.message}), None, None
    except JSONDecodeError as json_decode_error:
        return False, web.json_response({'address_error': json_decode_error.msg}), None, None
    except Exception:
        return False, web.json_response({'address_error': 'Exception'}), None, None
