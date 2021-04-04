"""
Creating sample data, users and API keys.
Afterward creating some sample addresses on the Go-Ethereum node by testing related API method.
More testing on get_balance method.
"""

import asyncio

from crypto_api.db import user
from tests.utils import clean_test_data, add_user, create_address, check_get_balance, USER_1, USER_2, \
    check_address_exists, get_user, get_all_addresses


# for these tests we need sample users
async def test_add_users(api):
    await clean_test_data(api)
    await asyncio.gather(add_user(api, USER_1), add_user(api, USER_2))
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user.select().where(user.c.username == USER_1))
        record = await result.first()
        assert record


async def test_create_address_for_two_users(api):
    user_1 = await get_user(api, USER_1)
    user_2 = await get_user(api, USER_2)
    await asyncio.gather(create_address(api, user_1), create_address(api, user_2))


async def test_create_many_addresses(api):
    printing = False
    amount_of_addresses_to_create = 10
    _user = await get_user(api, USER_2)
    await asyncio.gather(*(create_address(api, _user, i, printing) for i in range(amount_of_addresses_to_create)))

    # check new address was added to node
    addresses = await get_all_addresses(api, _user.id)
    results = await asyncio.gather(*(check_address_exists(addresses[i].blockchain_address)
                                     for i in range(len(addresses))))
    assert all(result for result in results)


async def test_get_balance_multiple_requests(api):
    await asyncio.gather(*(check_get_balance(api) for _ in range(50)))
