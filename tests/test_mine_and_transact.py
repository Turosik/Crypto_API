import asyncio

from tests.utils import USER_1, USER_2, get_user, get_address, start_mining, get_balance, stop_mining, print_balance, \
    send_transaction, get_transaction_status, check_transaction_in_db, get_all_addresses, \
    send_transaction_and_wait_it_got_mined


async def test_mine(api):
    mining_timer = 30  # seconds
    print_interval = 5  # seconds
    user_1 = await get_user(api, USER_1)
    address_1 = await get_address(api, user_1.id)
    start_balance = await get_balance(api, user_1, address_1)
    print('\nStarting balance {}'.format(start_balance))
    mining_result, _ = await asyncio.gather(start_mining(address_1, mining_timer),
                                            print_balance(api, user_1, address_1, mining_timer, print_interval))
    print(mining_result)
    finish_balance = await get_balance(api, user_1, address_1)
    print('After mining balance {}'.format(finish_balance))
    assert finish_balance > start_balance


async def test_send_transaction_and_check_status(api):
    import time
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1 = await get_user(api, USER_1)
    address_1 = await get_address(api, user_1.id)
    user_2 = await get_user(api, USER_2)
    address_2 = await get_address(api, user_2.id)

    start_balance = await get_balance(api, user_2, address_2)
    print('\nStarting balance {}'.format(start_balance))

    print('Transaction from {} to {}'.format(address_1.blockchain_address, address_2.blockchain_address))

    amount = 1
    tx_hash = await send_transaction(api, user_1, address_1, address_2, amount)
    assert tx_hash is not None
    if tx_hash:
        print('Transaction hash {}'.format(tx_hash))
        await check_transaction_in_db(api, tx_hash)

        tx_status = await get_transaction_status(api, user_1, tx_hash)
        print('Transaction status "{}"'.format(tx_status))
        assert tx_status is not None
        start = time.perf_counter()
        while tx_status != 'mined' and time.perf_counter() < start + max_wait_time_for_tx_being_mined:
            await asyncio.sleep(check_tx_status_interval)
            tx_status = await get_transaction_status(api, user_1, tx_hash)
            print('Transaction status "{0}" after {1:.2f} seconds of waiting'.format(tx_status,
                                                                                     time.perf_counter() - start))

    finish_balance = await get_balance(api, user_2, address_2)
    print('After transaction balance {}'.format(finish_balance))
    assert finish_balance > start_balance


async def test_send_many_transactions(api):
    import time
    amount_of_transactions_to_send = 50
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1 = await get_user(api, USER_1)
    address_1 = await get_address(api, user_1.id)
    user_2 = await get_user(api, USER_2)
    addresses = await get_all_addresses(api, user_2.id)

    start_balance = await get_balance(api, user_1, address_1)
    assert start_balance > 1
    amount_ether = round((start_balance / 2) / amount_of_transactions_to_send, 18)
    print('\nSending {} transactions with Ether amount {}'.format(amount_of_transactions_to_send, amount_ether))
    results = await asyncio.gather(
        *(send_transaction_and_wait_it_got_mined(api, user_1, address_1, addresses[i % len(addresses)], amount_ether,
                                                 max_wait_time_for_tx_being_mined, check_tx_status_interval)
          for i in range(amount_of_transactions_to_send)))

    assert all(result for result in results)

    await stop_mining()
