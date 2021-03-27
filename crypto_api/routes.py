from aiohttp import web

from handlers import handle, ping, api_key_check


def setup_routes(app):
    app.add_routes([web.get('/', handle),
                    web.get('/ping', ping),
                    web.post('/api-key', api_key_check)])
