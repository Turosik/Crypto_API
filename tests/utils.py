import asyncio

import aiohttp

from crypto_api.db import user_crypto_address, user, api_transactions
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
        result = await conn.execute(user_crypto_address.select().where(user_crypto_address.c.user == user_id)
                                    .order_by(user_crypto_address.c.id.asc()))
        record = await result.first()
        return record


async def get_all_addresses(api, user_id):
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user_crypto_address.select().where(user_crypto_address.c.user == user_id))
        records = await result.fetchall()
        return records


async def create_address(api, _user, sequence_number=0, printing=False) -> None:
    if printing:
        print('{} started'.format(sequence_number))

    # no password
    if printing:
        print('{} no password'.format(sequence_number))
    response = await api.post('', json={"method": "create_address",
                                        "api_key": _user.api_key})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Parameter password not found in POST data'}
    assert data == expected

    # create_address api method
    if printing:
        print('{} create address'.format(sequence_number))
    response = await api.post('', json={"method": "create_address",
                                        "api_key": _user.api_key,
                                        "password": "some_password_{}".format(sequence_number)})

    if printing:
        print('{} response {}'.format(sequence_number, response))
    assert response.status == 200
    data = await response.json()
    assert 'result' in data
    address = data['result']

    # check new address is in database
    if printing:
        print('{} checking db'.format(sequence_number))
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user_crypto_address.select()
                                    .where(user_crypto_address.c.blockchain_address == address))
        record = await result.first()
        assert record
        assert len(record.blockchain_private_key) == PRIVATE_KEY_LENGTH

    if printing:
        print('{} finished'.format(sequence_number))


async def check_address_exists(address) -> bool:
    json = {"jsonrpc": "2.0",
            "method": "eth_accounts",
            "params": [],
            "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:
            assert response.status == 200
            response = await response.json()
            assert 'error' not in response
            if 'result' in response:
                if address in response.get('result'):
                    return True

    return False


async def check_get_balance(api):
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


async def get_balance(api, _user, _address):
    response = await api.post('', json={"method": "get_balance",
                                        "api_key": _user.api_key,
                                        "address": _address.blockchain_address})
    assert response.status == 200
    data = await response.json()
    if 'error' not in data:
        return data['result']
    return 0


async def print_balance(api, _user, _address, timer, interval) -> None:
    import time
    start = time.perf_counter()
    while time.perf_counter() < start + timer:
        await asyncio.sleep(interval)
        balance = await get_balance(api, _user, _address)
        print('Balance {0} Ether after {1:.2f} seconds of mining'.format(balance, time.perf_counter() - start))


async def start_mining(_address, timer) -> bool:
    json = {"jsonrpc": "2.0",
            "method": "miner_setEtherbase",
            "params": [_address.blockchain_address],
            "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:
            assert response.status == 200
            response = await response.json()
            if 'error' not in response:
                print('Etherbase set to {}'.format(_address.blockchain_address))
            else:
                print('Error: {}'.format(response))
                return False

    json = {"jsonrpc": "2.0",
            "method": "miner_start",
            "params": [2],
            "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:
            assert response.status == 200
            response = await response.json()
            if 'error' not in response:
                print('Miner started')
            else:
                print('Error: {}'.format(response))
                return False

    await asyncio.sleep(timer)

    return True


async def stop_mining() -> bool:
    json = {"jsonrpc": "2.0",
            "method": "miner_stop",
            "params": [],
            "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=json) as response:
            assert response.status == 200
            response = await response.json()
            if 'error' not in response:
                print('Miner stopped')
            else:
                print('Error: {}'.format(response))
                return False
    return True


async def send_transaction(api, user_1, address_1, address_2, amount):
    # send_transaction api method
    response = await api.post('', json={"method": "send_transaction",
                                        "api_key": user_1.api_key,
                                        "address_from": address_1.blockchain_address,
                                        "address_to": address_2.blockchain_address,
                                        "amount": amount})
    assert response.status == 200
    data = await response.json()
    assert 'result' in data
    if 'result' in data:
        return data['result']
    return None


async def send_transaction_and_wait_it_got_mined(api, user_1, address_1, address_2, amount,
                                                 max_wait, check_interval) -> bool:
    import time

    # send_transaction api method
    response = await api.post('', json={"method": "send_transaction",
                                        "api_key": user_1.api_key,
                                        "address_from": address_1.blockchain_address,
                                        "address_to": address_2.blockchain_address,
                                        "amount": amount})
    assert response.status == 200
    data = await response.json()
    assert 'result' in data
    if 'result' in data:
        tx_hash = data['result']
        tx_status = await get_transaction_status(api, user_1, tx_hash)
        # print('{} transaction status "{}"'.format(tx_hash, tx_status))
        assert tx_status is not None
        start = time.perf_counter()
        while tx_status != 'mined' and time.perf_counter() < start + max_wait:
            await asyncio.sleep(check_interval)
            tx_status = await get_transaction_status(api, user_1, tx_hash)
            # print('{0} transaction status "{1}" after {2:.2f} seconds of waiting'.format(tx_hash, tx_status,
            #                                                                              time.perf_counter() - start))
        if tx_status == 'mined':
            return True
    return False


async def get_transaction_status(api, _user, tx_hash):
    response = await api.post('', json={"method": "get_transaction_status",
                                        "api_key": _user.api_key,
                                        "transaction_hash": tx_hash})
    assert response.status == 200
    data = await response.json()
    assert 'result' in data
    if data['result']:
        assert data['result'] in ['pending', 'mined', 'does not exist']
        return data['result']
    return None


async def check_transaction_in_db(api, tx_hash):
    # check new transaction is in database
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(api_transactions.select()
                                    .where(api_transactions.c.tx_hash == tx_hash))
        record = await result.first()
        assert record
