from time import sleep

from sqlalchemy import create_engine, MetaData
from crypto_api.db import user, user_crypto_address
from crypto_api.settings import config

DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"


def create_tables(_engine):
    meta = MetaData()
    meta.drop_all(bind=_engine, tables=[user, user_crypto_address])
    meta.create_all(bind=_engine, tables=[user, user_crypto_address])


def sample_data(_engine):
    conn = engine.connect()
    conn.execute(user.insert(), [{'username': 'Finn'}])
    conn.execute(user.insert(), [{'username': 'Jake'}])
    conn.close()


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_engine(db_url, echo=True)

    create_tables(engine)
    sample_data(engine)
