from aiohttp import web

from handlers import handle, ping


def setup_routes(app):
    app.add_routes([web.post('/', handle),
                    web.get('/ping', ping)])
