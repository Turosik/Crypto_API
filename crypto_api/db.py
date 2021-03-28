import aiopg.sa
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, DateTime
)
from sqlalchemy import func

from crypto_api.settings import API_KEY_LENGTH


__all__ = ['user', 'user_crypto_address']

meta = MetaData()


def generate_api_key():
    import random
    import string
    # from datetime import datetime
    # random.seed(datetime.now())
    return ''.join(random.choice(string.ascii_letters) for _ in range(API_KEY_LENGTH))
    # return str(datetime.now())


user = Table(
    'api_users', meta,
    Column('id', Integer, primary_key=True),
    Column('username', String(200), nullable=False),
    Column('api_key', String(API_KEY_LENGTH), nullable=False, default=generate_api_key()),
    Column('created', DateTime, nullable=False, server_default=func.now())
)


user_crypto_address = Table(
    'api_user_addresses', meta,
    Column('id', Integer, primary_key=True),
    Column('user', Integer, ForeignKey('api_users.id')),
    Column('created', DateTime, nullable=False, server_default=func.now()),
    Column('blockchain_address', String(200), nullable=False),
    Column('blockchain_private_key', String(200), nullable=False)
)


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
