import requests

# API endpoint and your API key
url = 'https://mainnet.infura.io/v3/d5cbe15a58dc43a6b15d4727b3896691'

# JSON-RPC request data
data = {
    "jsonrpc": "2.0",
    "method": "eth_getLogs",
    "params": [{
        'address': '0x0E8549b6AF6E648Ca42D1BE130ee25451265AD3F',
        'fromBlock': str(hex(19115895-7500)),
        'toBlock': str(hex(19115895)),
        # "blockHash": "0x7c5a35e9cb3e8ae0e221ab470abae9d446c3a5626ce6689fc777dcffcab52c70",
        # "topics": ["0x48dab321eda2a44b37d8d9fab92ca32ca3421cd2b7265198c26083c5b26cacf2"]
    }],
    "id": 0
}
# has_true = '0x48dab321eda2a44b37d8d9fab92ca32ca3421cd2b7265198c26083c5b26cacf2'
# Set the content type header
headers = {
    "Content-Type": "application/json"
}

# Send POST request
response = requests.post(url, json=data, headers=headers)

# Print response
print(response.json())
