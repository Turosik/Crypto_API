from web3 import Web3
from web3.auto import w3
'''
connected = w3.isConnected()
print(connected)
if connected and w3.clientVersion.startswith('Parity'):
    enode = w3.parity.enode

elif connected and w3.clientVersion.startswith('Geth'):
    enode = w3.geth.admin.nodeInfo

else:
    enode = None

print(enode)
'''
# web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
web3 = Web3(Web3.IPCProvider('/home/turosik/ETH/private/geth.ipc'))
print(web3.isConnected())
new_acc = web3.geth.personal.newAccount('1234')
print(new_acc)
