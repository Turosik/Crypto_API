import aiohttp

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


async def send_transaction(address_from, address_to, amount):
    pass