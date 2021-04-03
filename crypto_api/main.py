from aiohttp import web

from crypto_api.middlewares import error_middleware
from crypto_api.utils import config_logger
from settings import config
from routes import setup_routes
from db import close_pg, init_pg, init_pg_sync

app = web.Application()
setup_routes(app)
app['config'] = config
app.on_startup.append(init_pg)
# we still need sync connection to save nonce in sync with sending transactions
# TODO better use Redis for that instead of Postgres
app.on_startup.append(init_pg_sync)
app.on_cleanup.append(close_pg)
app.middlewares.append(error_middleware)


if __name__ == '__main__':
    log = config_logger()
    log.info('Server started...')
    web.run_app(app)
