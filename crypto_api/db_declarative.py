import aiopg.sa
from sqlalchemy import (
    Column, ForeignKey,
    Integer, String, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func

from crypto_api.settings import API_KEY_LENGTH

Base = declarative_base()


def generate_api_key():
    import random
    import string
    import time
    from datetime import datetime
    random.seed(datetime.now())
    # print(time.perf_counter_ns())
    return ''.join(random.choice(string.ascii_letters) for _ in range(API_KEY_LENGTH))
    # return str(datetime.now())


class User(Base):
    __tablename__ = 'api_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(200), nullable=False)
    api_key = Column(String(API_KEY_LENGTH), nullable=False, default=generate_api_key())
    created = Column(DateTime, nullable=False, server_default=func.now())
    blockchain_address = relationship('UserCryptoAddress')
    __mapper_args__ = {"eager_defaults": True}


class UserCryptoAddress(Base):
    __tablename__ = 'api_user_addresses'
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('api_users.id'))
    created = Column(DateTime, nullable=False, server_default=func.now())
    blockchain_address = Column(String(200), nullable=False)
    blockchain_private_key = Column(String(200), nullable=False)
    __mapper_args__ = {"eager_defaults": True}


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


# TODO find a way to move that to init_db.py
async def async_create_tables(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

