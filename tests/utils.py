import aiohttp

from crypto_api.db import user_crypto_address, user
from crypto_api.settings import PRIVATE_KEY_LENGTH, config

USER_1 = 'Finn'
USER_2 = 'Jake'

RPC_HOST = 'http://{IP}:{port}'
URL = RPC_HOST.format(**config['ethereum_url'])


async def clean_test_data(api):
    async with api.server.app['db'].acquire() as conn:
        await conn.execute(user.delete().where(user.c.username == USER_1))
        await conn.execute(user.delete().where(user.c.username == USER_2))


async def add_user(api, username):
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user.insert().values(username=username, api_key='sample_api_key_' + username))
        record = await result.fetchone()
        assert record


async def get_user(api, username):
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user.select().where(user.c.username == username))
        record = await result.first()
        return record


async def get_address(api, user_id):
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user_crypto_address.select().where(user_crypto_address.c.user == user_id))
        record = await result.first()
        return record


async def create_address(api, username) -> None:
    _user = await get_user(api, username)

    # no password
    response = await api.post('', json={"method": "create_address",
                                        "api_key": _user.api_key})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Parameter password not found in POST data'}
    assert data == expected

    # create_address api method
    response = await api.post('', json={"method": "create_address",
                                        "api_key": _user.api_key,
                                        "password": "some_password"})

    assert response.status == 200
    data = await response.json()
    assert 'result' in data
    address = data['result']

    # check new address is in database
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user_crypto_address.select()
                                    .where(user_crypto_address.c.blockchain_address == address))
        record = await result.first()
        assert record
        assert len(record.blockchain_private_key) == PRIVATE_KEY_LENGTH

    # check new address was added to node
    json = {"jsonrpc": "2.0",
            "method": "eth_accounts",
            "params": [],
            "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:
            assert response.status == 200
            response = await response.json()
            assert 'error' not in response
            assert address in response.get('result')


async def get_balance(api):
    _user_1 = await get_user(api, USER_1)
    _address_1 = await get_address(api, _user_1.id)
    _user_2 = await get_user(api, USER_2)

    # check own balance
    response = await api.post('', json={"method": "get_balance",
                                        "api_key": _user_1.api_key,
                                        "address": _address_1.blockchain_address})
    assert response.status == 200
    data = await response.json()
    # of course it is zero... where can we get tokens?
    expected = {'result': 0.0}
    assert data == expected

    # check foreign balance... also it's address owner check
    response = await api.post('', json={"method": "get_balance",
                                        "api_key": _user_2.api_key,
                                        "address": _address_1.blockchain_address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'This is not your address'}
    assert data == expected

    # some garbage instead of address... also it's address owner check
    response = await api.post('', json={"method": "get_balance",
                                        "api_key": _user_1.api_key,
                                        "address": "some garbage"})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'This is not your address'}
    assert data == expected

