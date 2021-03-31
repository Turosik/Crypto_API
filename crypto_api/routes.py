from aiohttp import web

from handlers import handle, ping, api_create_address, api_get_balance, api_send_transaction, \
    api_get_transaction_status


def setup_routes(app):
    app.add_routes([web.post('/', handle),
                    web.get('/ping', ping)])
    '''
                    web.post('/create-address', api_create_address),
                    web.post('/get-balance', api_get_balance),
                    web.post('/send-transaction', api_send_transaction),
                    web.post('/get-transaction-status', api_get_transaction_status)])
'''