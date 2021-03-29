from aiohttp import web

from handlers import handle, ping, api_key_check_handler, api_create_address


def setup_routes(app):
    app.add_routes([web.get('/', handle),
                    web.get('/ping', ping),
                    web.post('/api-key', api_key_check_handler),
                    web.post('/create-address', api_create_address)])
