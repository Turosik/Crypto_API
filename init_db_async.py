import asyncio
from time import sleep

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from crypto_api.settings import config
from crypto_api.db import User, UserCryptoAddress, async_create_tables

DSN = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
Base = declarative_base()


async def sample_data(async_engine, username):
    async_session = sessionmaker(
        async_engine, class_=AsyncSession
    )

    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    User(username=username),
                ]
            )


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_async_engine(
        db_url,
        echo=True,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_create_tables(engine))
    # TODO create second user with another random seed
    # TODO may be just use sync methods
    loop.run_until_complete(sample_data(engine, 'Finn'))
    # loop.run_until_complete(sample_data(engine, 'Jake'))
