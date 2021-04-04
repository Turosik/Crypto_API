"""
IMPORTANT! Run it ONLY AFTER test_addresses_and_balance.py because this test requires sample data.
Setting one of the previously created test addresses as Ether base for the node.
Mining for half a minute or so to get some Ether.
Now we can test transacting part of API.
"""

import asyncio

from tests.utils import USER_1, USER_2, get_user, get_address, start_mining, get_balance, stop_mining, print_balance, \
    send_transaction, get_transaction_status, check_transaction_in_db, get_all_addresses, \
    send_transaction_and_wait_it_got_mined

PRINTING = True


async def get_stuff(api):
    user_1 = await get_user(api, USER_1)
    assert user_1, 'You should run test_addresses_and_balance.py first, in order to create sample users!'
    address_1 = await get_address(api, user_1.id)
    user_2 = await get_user(api, USER_2)
    assert user_2, 'You should run test_addresses_and_balance.py first, in order to create sample users!'
    address_2 = await get_address(api, user_2.id)
    addresses = await get_all_addresses(api, user_2.id)
    return user_1, address_1, user_2, address_2, addresses


# mine some Ether
async def test_mine(api):
    mining_timer = 30  # seconds
    print_interval = 5  # seconds
    user_1, address_1, _, _, _ = await get_stuff(api)

    start_balance = await get_balance(api, user_1, address_1)
    print('\nStarting balance {}'.format(start_balance))
    mining_result, _ = await asyncio.gather(start_mining(address_1, mining_timer),
                                            print_balance(api, user_1, address_1, mining_timer, print_interval))
    print(mining_result)
    finish_balance = await get_balance(api, user_1, address_1)
    print('After mining balance {}'.format(finish_balance))
    assert finish_balance > start_balance


# send single transaction and look how it got mined
async def test_send_transaction_and_check_status(api):
    import time
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1, address_1, user_2, address_2, _ = await get_stuff(api)

    start_balance = await get_balance(api, user_2, address_2)
    if PRINTING:
        print('\nStarting balance {}'.format(start_balance))

    if PRINTING:
        print('Transaction from {} to {}'.format(address_1.blockchain_address, address_2.blockchain_address))

    amount = 1
    # send transaction and get it's hash
    tx_hash = await send_transaction(api, user_1, address_1, address_2, amount)
    assert tx_hash is not None
    if tx_hash:
        if PRINTING:
            print('Transaction hash {}'.format(tx_hash))
        await check_transaction_in_db(api, tx_hash)

        # check status, guess it will be "pending"
        tx_status = await get_transaction_status(api, user_1, tx_hash)
        if PRINTING:
            print('Transaction status "{}"'.format(tx_status))
        assert tx_status is not None

        # check status in a loop until it got mined or time will run out
        start = time.perf_counter()
        while tx_status != 'mined' and time.perf_counter() < start + max_wait_time_for_tx_being_mined:
            await asyncio.sleep(check_tx_status_interval)
            tx_status = await get_transaction_status(api, user_1, tx_hash)
            if PRINTING:
                print('Transaction status "{0}" after {1:.2f} seconds of waiting'
                      .format(tx_status, time.perf_counter() - start))

    # compare balance before transaction and after
    finish_balance = await get_balance(api, user_2, address_2)
    if PRINTING:
        print('After transaction balance {}'.format(finish_balance))
    assert finish_balance > start_balance


# send many transactions asynchronously
async def test_send_many_transactions(api):
    amount_of_transactions_to_send = 20
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1, address_1, user_2, _, addresses = await get_stuff(api)

    start_balance = await get_balance(api, user_1, address_1)
    assert start_balance > 1
    # we are going to use only half of the balance for that
    amount_ether = round((start_balance / 2) / amount_of_transactions_to_send, 18)
    if PRINTING:
        print('\nSending {} transactions with Ether amount {}'.format(amount_of_transactions_to_send, amount_ether))

    # all magic is in send_transaction_and_wait_it_got_mined function
    results = await asyncio.gather(
        *(send_transaction_and_wait_it_got_mined(api, user_1, address_1, addresses[i % len(addresses)], amount_ether,
                                                 max_wait_time_for_tx_being_mined, check_tx_status_interval)
          for i in range(amount_of_transactions_to_send)))

    if PRINTING:
        print('Results True - {}'.format(sum(1 for result in results if result)))
        print('Results False - {}'.format(sum(1 for result in results if not result)))

    # assert all transactions were successfully mined
    assert all(result for result in results)


# now we will send a series of transactions with total amount greater than our balance
# and watch how exceeding transactions will be rejected by the network
async def test_send_transactions_over_balance(api):
    import time
    amount_of_transactions_to_send = 4  # must be >= 3
    assert amount_of_transactions_to_send >= 3
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1, address_1, user_2, _, addresses = await get_stuff(api)

    start_balance = await get_balance(api, user_1, address_1)
    if PRINTING:
        print('\nStarting balance {}'.format(start_balance))
    assert start_balance > 1
    amount_ether = round(start_balance / (amount_of_transactions_to_send - 2), 18)
    if PRINTING:
        print('Calculated amount of {} Ether, last 1 or 2 transactions will exceed the balance'.format(amount_ether))

    tx_hashes = await asyncio.gather(
        *(send_transaction(api, user_1, address_1, addresses[i % len(addresses)], amount_ether)
          for i in range(amount_of_transactions_to_send)))
    if PRINTING:
        print('Transaction hashes {}'.format(tx_hashes))

    tx_statuses = await asyncio.gather(
        *(get_transaction_status(api, user_1, tx_hashes[i]) for i in range(len(tx_hashes))))
    if PRINTING:
        print('Transaction statuses {}'.format(tx_statuses))

    start = time.perf_counter()
    while not all(tx_status in ['mined', 'does not exist'] for tx_status in tx_statuses) \
            and time.perf_counter() < start + max_wait_time_for_tx_being_mined:
        await asyncio.sleep(check_tx_status_interval)
        tx_statuses = await asyncio.gather(
            *(get_transaction_status(api, user_1, tx_hashes[i]) for i in range(len(tx_hashes))))
        if PRINTING:
            print('Transaction statuses "{0}" after {1:.2f} seconds of waiting'
                  .format(tx_statuses, time.perf_counter() - start))

    assert all(tx_status in ['mined', 'does not exist'] for tx_status in tx_statuses)


# send some more transactions to be sure that after rejected ones our nonce is fine
async def test_send_many_transactions_again(api):
    amount_of_transactions_to_send = 3
    max_wait_time_for_tx_being_mined = 60  # seconds
    check_tx_status_interval = 5  # seconds
    user_1, address_1, user_2, _, addresses = await get_stuff(api)

    start_balance = await get_balance(api, user_1, address_1)
    assert start_balance > 1
    # we are going to use only half of the balance for that
    amount_ether = round((start_balance / 2) / amount_of_transactions_to_send, 18)
    if PRINTING:
        print('\nSending {} transactions with Ether amount {}'.format(amount_of_transactions_to_send, amount_ether))

    # all magic is in send_transaction_and_wait_it_got_mined function
    results = await asyncio.gather(
        *(send_transaction_and_wait_it_got_mined(api, user_1, address_1, addresses[i % len(addresses)], amount_ether,
                                                 max_wait_time_for_tx_being_mined, check_tx_status_interval)
          for i in range(amount_of_transactions_to_send)))

    if PRINTING:
        print('Results True - {}'.format(sum(1 for result in results if result)))
        print('Results False - {}'.format(sum(1 for result in results if not result)))

    # assert all transactions were successfully mined
    assert all(result for result in results)

    # is that really necessary?
    # await stop_mining()
