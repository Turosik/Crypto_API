import inspect
import logging
import aiopg.sa
from aiohttp import web
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, DateTime
)
from sqlalchemy import func

from crypto_api.settings import API_KEY_LENGTH

meta = MetaData()


def generate_api_key():
    import random
    import string
    from datetime import datetime
    random.seed(datetime.now())
    return ''.join(random.choice(string.ascii_letters) for _ in range(API_KEY_LENGTH))


# API users and keys
user = Table(
    'api_users', meta,
    Column('id', Integer, primary_key=True),
    Column('username', String(200), nullable=False),
    Column('api_key', String(API_KEY_LENGTH), nullable=False, default=generate_api_key()),
    Column('created', DateTime, nullable=False, server_default=func.now())
)


# store addresses created using API
user_crypto_address = Table(
    'api_user_addresses', meta,
    Column('id', Integer, primary_key=True),
    Column('user', Integer, ForeignKey('api_users.id', ondelete='CASCADE')),
    Column('created', DateTime, nullable=False, server_default=func.now()),
    Column('blockchain_address', String(42), nullable=False),
    Column('blockchain_private_key', String(64), nullable=False)
)


# transactions sent by API, main purpose is storing nonce
api_transactions = Table(
    'api_transactions', meta,
    Column('id', Integer, primary_key=True),
    Column('created', DateTime, nullable=False, server_default=func.now()),
    Column('address_from', Integer, ForeignKey('api_user_addresses.id', ondelete='CASCADE')),
    Column('address_to', String(42), nullable=False),
    Column('nonce', Integer, nullable=False),
    Column('tx_hash', String(66), nullable=False)
)


class RecordNotFound(Exception):
    def __init__(self, caller, description):
        self.caller = caller
        self.message = description

        # use only logger for output, further behavior depends on logger settings
        logger = logging.getLogger(__package__)
        logger.error(self.__str__())

    def __str__(self):
        return 'RECORD NOT FOUND (module {}): {}'.format(self.caller, self.message)


async def save_new_address(new_address, private_key, user_id, database):
    async with database.acquire() as conn:
        result = await conn.execute(user_crypto_address.insert().values(user=user_id, blockchain_address=new_address,
                                                                        blockchain_private_key=private_key))
        record = await result.fetchone()
        if not record:
            raise RecordNotFound(inspect.stack()[1].function, 'Error saving new address for user {}'.format(user_id))

        return web.json_response({'result': new_address})


async def save_new_transaction(address_id, address_to, nonce, tx_hash, database):
    async with database.acquire() as conn:
        result = await conn.execute(api_transactions.insert().values(address_from=address_id, address_to=address_to,
                                                                     nonce=nonce, tx_hash=tx_hash))
        record = await result.fetchone()
        if not record:
            raise RecordNotFound(inspect.stack()[1].function, 'Error saving new transaction {}'.format(tx_hash))

        return web.json_response({'result': tx_hash})


async def get_address_attributes(address, database):
    async with database.acquire() as conn:
        result = await conn.execute(user_crypto_address.select()
                                    .where(user_crypto_address.columns.blockchain_address == address))
        record = await result.first()
        if not record:
            raise RecordNotFound(inspect.stack()[1].function,
                                 'Error getting private key for address {}'.format(address))

        return record.id, record.blockchain_private_key


# get nonce from database
async def get_nonce(address_id, database) -> int:
    async with database.acquire() as conn:
        result = await conn.execute(api_transactions.select()
                                    .where(api_transactions.columns.address_from == address_id)
                                    .order_by(api_transactions.columns.nonce.desc()))
        record = await result.fetchone()
        if not record:
            return -1

        return record.nonce


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
    )
    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
