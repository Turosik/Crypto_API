async def test_ping(api):
    response = await api.get('/ping')
    assert response.status == 200
    data = await response.json()
    expected = {'ping': 'pong'}
    assert data == expected


async def test_incorrect_inputs(api):
    address = "0xSomeAddress"
    api_key = "0xSomeKey"

    # test some non json string
    response = await api.post('', data='is not json at all')
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'JSON decode error'}
    assert data == expected

    # test integer
    response = await api.post('', data='123')
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Unsupported argument type'}
    assert data == expected

    # no method empty method and incorrect method
    response = await api.post('', json={"api_key": api_key,
                                        "address": address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Parameter method not found in POST data'}
    assert data == expected

    response = await api.post('', json={"method": "",
                                        "api_key": api_key,
                                        "address": address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Parameter method is empty'}
    assert data == expected

    response = await api.post('', json={"method": "incorrect_method",
                                        "api_key": api_key,
                                        "address": address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'Unknown method incorrect_method'}
    assert data == expected


async def test_api_key(api):
    address = "0xSomeAddress"

    # no api key
    response = await api.post('', json={"method": "get_balance",
                                        "address": address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'API key not found in POST data'}
    assert data == expected

    # incorrect api key
    response = await api.post('', json={"method": "get_balance",
                                        "api_key": "incorrect_api_key",
                                        "address": address})
    assert response.status == 200
    data = await response.json()
    expected = {'API_error': 'API key does not exist'}
    assert data == expected
