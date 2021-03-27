from aiohttp import web

from crypto_api.middlewares import error_middleware
from settings import config
from routes import setup_routes
from db import close_pg, init_pg

app = web.Application()
setup_routes(app)
app['config'] = config
app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
app.middlewares.append(error_middleware)

if __name__ == '__main__':
    web.run_app(app)
