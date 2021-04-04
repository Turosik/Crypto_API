from sqlalchemy import create_engine, MetaData
from crypto_api.db import user, user_crypto_address, api_transactions
from crypto_api.settings import config

DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"


# create database tables
def create_tables(_engine):
    meta = MetaData()
    meta.drop_all(bind=_engine, tables=[user, user_crypto_address, api_transactions])
    meta.create_all(bind=_engine, tables=[user, user_crypto_address, api_transactions])


# we will create sample data only in tests
def sample_data(_engine):
    # conn = engine.connect()
    # conn.execute(user.insert(), [{'username': 'Finn', 'api_key': 'sample_api_key_finn'}])
    # conn.execute(user.insert(), [{'username': 'Jake', 'api_key': 'sample_api_key_jake'}])
    # conn.close()
    pass


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_engine(db_url, echo=True)

    create_tables(engine)
    sample_data(engine)
