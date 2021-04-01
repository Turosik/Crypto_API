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
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"get_balance","api_key":"sample_api_key","address":"0x48704b2c3915f709fa9b3b96a9340686ad9013d7"}' 0.0.0.0:8080</code></p>
<p>Returns balance of given address in Ether.</p>
<hr>
