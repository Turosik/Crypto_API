import inspect
import logging

from crypto_api import db
from crypto_api.db import user, user_crypto_address
from crypto_api.settings import config, BASE_DIR

logger = logging.getLogger(__package__)


def config_logger():
    _logger = logging.getLogger(__package__)
    _logger.setLevel(config['logger']['level'])
    formatter = logging.Formatter('%(asctime)-23s %(levelname)-8s %(message)s')

    # try to create file handler
    try:
        file_handler = logging.FileHandler(filename=BASE_DIR / config['logger']['file_name'], mode="a+")
        print('using log file name: {}'.format(file_handler.baseFilename))
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    except FileNotFoundError:
        print('can not create log file')

    # additionally create stream handler if log to stream was set True
    if config['logger']['stream']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(config['logger']['level'])
        stream_handler.setFormatter(formatter)
        _logger.addHandler(stream_handler)

    return _logger


class CryptoApiException(Exception):
    def __init__(self, caller, description):
        self.caller = caller
        self.message = description

        # use only logger for output, further behavior depends on logger settings
        logger.error(self.__str__())

    def __str__(self):
        return 'API EXCEPTION (module {}): {}'.format(self.caller, self.message)


# get any value from POST data by name
async def get_value_from_post_data(post_data, param_name):
    if param_name not in post_data:
        raise CryptoApiException(inspect.stack()[1].function,
                                 'Parameter {} not found in POST data'.format(param_name))

    if not post_data[param_name]:
        raise CryptoApiException(inspect.stack()[1].function,
                                 'Parameter {} is empty'.format(param_name))

    return post_data[param_name]


# check that api key is correct
async def api_key_check(post_data, database):
    if 'api_key' not in post_data:
        raise CryptoApiException(inspect.stack()[1].function, 'API key not found in POST data')

    async with database.acquire() as conn:
        result = await conn.execute(db.user.select().where(user.columns.api_key == post_data['api_key']))
        found_key = await result.first()

        if not found_key:
            raise CryptoApiException(inspect.stack()[1].function, 'API key does not exist')

        return True, found_key.id


# check that address and api key belongs to one user
async def address_owner_check(user_id, post_data, database, param_name):
    if param_name not in post_data:
        raise CryptoApiException(inspect.stack()[1].function, 'Address not found in POST data')

    async with database.acquire() as conn:
        result = await conn.execute(db.user_crypto_address.select()
                                    .where(user_crypto_address.columns.blockchain_address == post_data[param_name])
                                    .where(user_crypto_address.columns.user == user_id))
        found_address = await result.first()

        if not found_address:
            raise CryptoApiException(inspect.stack()[1].function, 'This is not your address')

        return True, found_address.blockchain_address, found_address.id
