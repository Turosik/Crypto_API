from aiohttp import web

from handlers import handle, ping, api_key_check_handler, api_create_address, api_get_balance, api_send_transaction


def setup_routes(app):
    app.add_routes([web.get('/', handle),
                    web.get('/ping', ping),
                    web.post('/api-key', api_key_check_handler),
                    web.post('/create-address', api_create_address),
                    web.post('/get-balance', api_get_balance),
                    web.post('/send-transaction', api_send_transaction)])
