import asyncio

from crypto_api.db import user
from tests.utils import clean_test_data, add_user, create_address, get_balance, USER_1, USER_2


async def test_add_users(api):
    await clean_test_data(api)
    await asyncio.gather(add_user(api, USER_1), add_user(api, USER_2))
    async with api.server.app['db'].acquire() as conn:
        result = await conn.execute(user.select().where(user.c.username == USER_1))
        record = await result.first()
        assert record


async def test_create_address_for_two_users(api):
    await asyncio.gather(create_address(api, USER_1), create_address(api, USER_2))


async def test_create_multiple_addresses(api):
    await asyncio.gather(*(create_address(api, USER_1) for _ in range(3)))


async def test_get_balance_multiple_requests(api):
    await asyncio.gather(*(get_balance(api) for _ in range(50)))
