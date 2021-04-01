import inspect
import logging

import aiohttp
from aiohttp import web
from web3 import Web3

from crypto_api.db import get_address_attributes, get_nonce, RecordNotFound
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


async def send_transaction(address_from, address_to, amount, database):
    web3 = Web3(Web3.IPCProvider(config['ethereum']['IPCProvider']))
    print(web3.isConnected())

    try:
        address_id, private_key = await get_address_attributes(address_from, database)
    except RecordNotFound:
        return None, None, web.json_response({'API_error': 'Private key not found'})
    if not private_key:
        return None, None, web.json_response({'API_error': 'Private key is empty'})
    private_key = '0x' + private_key

    checksum_address = web3.toChecksumAddress(address_from)
    current_nonce = await get_nonce(address_id, database)
    tx_count = web3.eth.getTransactionCount(checksum_address)
    nonce = max(current_nonce, tx_count) + 1

    checksum_address = web3.toChecksumAddress(address_to)

    print(web3.eth.gasPrice)

    transaction = {'to': checksum_address,
                   'value': web3.toWei(amount, 'ether'),  # int(round(amount * WEI)),
                   'gas': config['ethereum']['gas'],
                   'gasPrice': max(web3.eth.gasPrice, config['ethereum']['gasPrice']),
                   'nonce': nonce,
                   'chainId': int(config['ethereum']['chainId'])
                   }

    signed = web3.eth.account.sign_transaction(transaction, private_key)

    try:
        web3.eth.sendRawTransaction(signed.rawTransaction)
        tx_hash = web3.toHex(web3.sha3(signed.rawTransaction))
    except ValueError as exception:
        logger = logging.getLogger(__package__)
        logger.error('Send transaction error: {}'.format(exception))
        return None, None, web.json_response({'API_error': str(exception)})  # 'insufficient funds'})
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

