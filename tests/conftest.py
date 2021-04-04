import pytest
from aiohttp import web

from crypto_api.db import init_pg, close_pg
from crypto_api.middlewares import error_middleware
from crypto_api.routes import setup_routes
from crypto_api.settings import config


@pytest.fixture
def api(loop, aiohttp_client):
    app = web.Application()
    setup_routes(app)
    app['config'] = config
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    app.middlewares.append(error_middleware)
    return loop.run_until_complete(aiohttp_client(app))
