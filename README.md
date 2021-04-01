# Crypto API
<p>Notice! You should have Go-Ethereum node installed and running.</p>
<p><b>Installation</b></p>
<hr>
<p><b>API Methods</b></p>
<p>Create new address on Ethereum blockchain.<br>
Parameters:<br>
<code>
"method": "create_address"  &nbsp;
"api_key": "your_api_key"  
"password": "your_new_password"
</code><br></p>
<p>Example<br>
<code>curl -X POST -H "Content-Type:application/json" --data '{"method":"create_address","api_key":"sample_api_key","password":"qwerty"}' 0.0.0.0:8080</code></p>
<p>Returns your new address.</p>
<hr>
