from web3 import Web3
from web3.auto import w3

# connected = w3.isConnected()
# print(connected)
web3 = Web3(Web3.IPCProvider('/home/turosik/PycharmProjects/Ibit_task/ETH/geth.ipc'))
print(web3.isConnected())

checksum_address = web3.toChecksumAddress('0x87c4496859d5ee16f96a3b49ec8e690470b21b53')
print(checksum_address)
transaction = {'to': checksum_address,
               'value': 1000000000000000000000,
               'gas': 2000000,
               'gasPrice': 23456789765,
               'nonce': 1,
               'chainId': 4224
               }
key = '0xdf6382e3ed7d145f6bd671aff412e1594c5e18f6da4be4d1eb43428ef7cd1a25'

signed = web3.eth.account.sign_transaction(transaction, key)
print(signed.rawTransaction)

tx_hash = web3.eth.sendRawTransaction(signed.rawTransaction)
tx_id = web3.toHex(web3.sha3(signed.rawTransaction))
print(tx_hash)
print(tx_id)

'''
# web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
web3 = Web3(Web3.IPCProvider('/home/turosik/ETH/private/geth.ipc'))
print(web3.isConnected())
new_acc = web3.geth.personal.newAccount('1234')
print(new_acc)
'''