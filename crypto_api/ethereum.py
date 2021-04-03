import inspect
import logging

import aiohttp
from aiohttp import web
from web3 import Web3

from crypto_api.db import get_address_attributes, RecordNotFound, save_new_transaction_sync, get_nonce_sync
from crypto_api.settings import config, WEI, PRIVATE_KEY_LENGTH
from crypto_api.utils import CryptoApiException

RPC_HOST = 'http://{IP}:{port}'
URL = RPC_HOST.format(**config['ethereum_url'])


async def create_new_private_key() -> str:
    import random
    import string
    from datetime import datetime
    random.seed(datetime.now())
    return ''.join(random.choice(string.hexdigits) for _ in range(PRIVATE_KEY_LENGTH)).lower()


# Universal function to get the result of JSON-RPC method used by other handler functions
async def get_result(json):
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:

            if response.status != 200:
                raise CryptoApiException(inspect.stack()[1].function,
                                         'Connection error, status {}'.format(response.status))

            response = await response.json()

            error = response.get('error')
            if error:
                raise CryptoApiException(inspect.stack()[1].function,
                                         'Error: {}'.format('unknown' if 'message' not in error
                                                            else error['message']))

            return response.get('result')


async def create_new_address(password):
    try:
        private_key = await create_new_private_key()
        json = {"jsonrpc": "2.0",
                "method": "personal_importRawKey",
                "params": [private_key, password],
                "id": 1}

        result = await get_result(json)
        if result:
            return result, private_key, None
        else:
            raise CryptoApiException(inspect.stack()[1].function,
                                     'Unexpected result when adding new address')

    except CryptoApiException as api_exception:
        return None, None, web.json_response({'API_error': api_exception.message})


async def get_balance(address):
    try:
        json = {"jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1}
        result = await get_result(json)
        if result:
            return web.json_response({'result': int(result, 0) / WEI})
        else:
            raise CryptoApiException(inspect.stack()[1].function,
                                     'Unexpected result when getting balance')

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})


# send transactions is using Web3 lib
# save transactions synchronous because we mush save nonce before trying to send next transaction
async def send_transaction(address_from, address_to, amount, database, database_sync):
    web3 = Web3(Web3.IPCProvider(config['ethereum']['IPCProvider']))

    try:
        address_id, private_key = await get_address_attributes(address_from, database)
    except RecordNotFound:
        return None, None, web.json_response({'API_error': 'Private key not found'})
    if not private_key:
        return None, None, web.json_response({'API_error': 'Private key is empty'})
    hex_private_key = '0x' + private_key

    checksum_address = web3.toChecksumAddress(address_from)
    # current_nonce = await get_nonce(address_id, database)
    current_nonce = get_nonce_sync(address_id, database_sync)
    tx_count = web3.eth.get_transaction_count(checksum_address)
    # it's not fast but very safe to choose for nonce the maximum value between saved in DB and the one from node
    nonce = max(current_nonce + 1, tx_count)

    checksum_address = web3.toChecksumAddress(address_to)

    # print('gasPrice {}'.format(web3.eth.gasPrice))
    # print('nonce {}'.format(nonce))

    transaction = {'to': checksum_address,
                   'value': web3.toWei(amount, 'ether'),  # int(round(amount * WEI)),
                   'gas': config['ethereum']['gas'],
                   'gasPrice': max(web3.eth.gasPrice, config['ethereum']['gasPrice']),
                   'nonce': nonce,
                   'chainId': int(config['ethereum']['chainId'])
                   }

    signed = web3.eth.account.sign_transaction(transaction, hex_private_key)

    try:
        web3.eth.sendRawTransaction(signed.rawTransaction)
        tx_hash = web3.toHex(web3.sha3(signed.rawTransaction))
        # await save_new_transaction(address_id, address_to, nonce, tx_hash, database)
        save_new_transaction_sync(address_id, address_to, nonce, tx_hash, database_sync)
    except ValueError as exception:
        logger = logging.getLogger(__package__)
        logger.error('Send transaction error: {}'.format(exception))
        return None, None, web.json_response({'API_error': str(exception)})  # 'insufficient funds'})
    except RecordNotFound:
        return None, None, web.json_response({'API_error': 'Internal server error'})

    return tx_hash, nonce, web.json_response({'result': tx_hash})


async def get_transaction_status(tx_hash):
    try:
        json = {"jsonrpc": "2.0",
                "method": "eth_getTransactionByHash",
                "params": [tx_hash],
                "id": 1}
        result = await get_result(json)
        if 'blockNumber' not in result:
            raise CryptoApiException(inspect.stack()[1].function,
                                     'Parameter blockNumber not found')
        if result['blockNumber']:
            return web.json_response({'result': 'mined'})
        else:
            return web.json_response({'result': 'pending'})

    except CryptoApiException as api_exception:
        return web.json_response({'API_error': api_exception.message})
