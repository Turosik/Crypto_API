# Crypto API
<p>Notice! You should have Go-Ethereum node installed and running.</p>
<p><b>Installation</b></p>
<hr>
<p><b>API Methods</b></p>
<p>Create new address on Ethereum blockchain.<br>
Parameters:<br>
"method": "create_address"<br>
"api_key": "your_api_key"<br>
"password": "your_new_password"<br></p>
<p>Example<br>
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"create_address","api_key":"sample_api_key","password":"qwerty"}' 0.0.0.0:8080</code></p>
<p>Returns your new address.</p>
<hr>
<p>Get balance of the address. Notice that you can get balance addresses created under your API key only.<br>
Parameters:<br>
"method": "get_balance"<br>
"api_key": "your_api_key"<br>
"address": "one_of_your_addresses"<br></p>
<p>Example<br>
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"get_balance","api_key":"sample_api_key","address":"0x48704b2c3915f709fa9b3b96a9340686ad9013d7"}' 0.0.0.0:8080</code></p>
<p>Returns balance of given address in Ether.</p>
<hr>
<p>Send transaction of Ether from your address to another one. You can send transactions only from your own addresses.<br>
Parameters:<br>
"method": "send_transaction"<br>
"api_key": "your_api_key"<br>
"address_from": "one_of_your_addresses"<br>
"address_to": "address_where_you_want_to_send"<br>
"amount": value in Ether<br></p>
<p>Example<br>
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"send_transaction","api_key":"sample_api_key","address_from":"0x48704b2c3915f709fa9b3b96a9340686ad9013d7","address_to":"0xf905fbb8b52ea4df323dae7201b2fbb068843755","amount":25}' 0.0.0.0:8080</code></p>
<p>Returns the hash of transaction.</p>
<hr>
<p>Check the status of the transaction.<br>
Parameters:<br>
"method": "get_transaction_status"<br>
"api_key": "your_api_key"<br>
"transaction_hash": "transaction_hash"<br></p>
<p>Example<br>
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"get_transaction_status","api_key":"sample_api_key","transaction_hash":"0x78e6be84da33df26d8696d1df7fd4023d5f81028c2c18284c67189d14ec25363"}' 0.0.0.0:8080</code></p>
<p>Returns status of the transaction.</p>
