import aiohttp
from aiohttp import web
from web3 import Web3

from crypto_api.db import get_address_attributes, get_nonce, RecordNotFound
from crypto_api.settings import config, GWEI

RPC_HOST = 'http://{IP}:{port}'
URL = RPC_HOST.format(**config['ethereum_url'])


async def create_new_private_key() -> str:
    import random
    import string
    from datetime import datetime
    random.seed(datetime.now())
    return ''.join(random.choice(string.hexdigits) for _ in range(64)).lower()


async def create_new_address(password):
    private_key = await create_new_private_key()
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json={"jsonrpc": "2.0",
                                           "method": "personal_importRawKey",
                                           "params": [private_key, password],
                                           "id": 1}) as response:
            # TODO response status and error handling
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            response = await response.json()
            print(response)
            print(response.get('result'))

    return response.get('result'), private_key


async def get_balance(address):
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json={"jsonrpc": "2.0",
                                           "method": "eth_getBalance",
                                           "params": [address, "latest"],
                                           "id": 1}) as response:
            # TODO response status and error handling
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            response = await response.json()
            print(response)
            print(response.get('result'))
            # TODO convert to decimal

    return int(response.get('result'), 0) / GWEI


async def send_transaction(address_from, address_to, amount, database):
    web3 = Web3(Web3.IPCProvider(config['ethereum']['IPCProvider']))
    print(web3.isConnected())

    checksum_address = web3.toChecksumAddress(address_to)
    print(checksum_address)

    try:
        address_id, private_key = await get_address_attributes(address_from, database)
    except RecordNotFound:
        return None, web.json_response({'API_error': 'Private key not found'})
    if not private_key:
        return None, web.json_response({'API_error': 'Private key is empty'})
    private_key = '0x' + private_key
    nonce = await get_nonce(address_id, database)
    nonce += 1

    transaction = {'to': checksum_address,
                   'value': web3.toWei(amount, 'ether'),  # int(round(amount * GWEI)),
                   'gas': 2000000,
                   'gasPrice': web3.eth.gasPrice,
                   'nonce': nonce,
                   'chainId': int(config['ethereum']['chainId'])
                   }

    signed = web3.eth.account.sign_transaction(transaction, private_key)
    print(signed.rawTransaction)

    # TODO rewrite to JSON-RPC
    web3.eth.sendRawTransaction(signed.rawTransaction)
    # ValueError: {'code': -32000, 'message': 'nonce too low'}
    tx_hash = web3.toHex(web3.sha3(signed.rawTransaction))
    print(tx_hash)
    return tx_hash, nonce, web.json_response({'transaction': tx_hash})
