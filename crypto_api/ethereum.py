import aiohttp

from crypto_api.settings import config

RPC_HOST = 'http://{IP}:{port}'


async def create_new_private_key() -> str:
    import random
    import string
    from datetime import datetime
    random.seed(datetime.now())
    return ''.join(random.choice(string.hexdigits) for _ in range(64)).lower()


async def create_new_address(password):
    url = RPC_HOST.format(**config['ethereum'])
    private_key = await create_new_private_key()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"jsonrpc": "2.0",
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
