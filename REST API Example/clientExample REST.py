import requests
import base64
import time

class args:
    url = "https://webapi.coinflex.com"  # change URL between STAGE and LIVE
    cookie = ''  # this is the API key from your CoinFLEX account found in API Details
    id = ''  # this is user ID for your CoinFLEX account found in API Details
    phrase = ''  # this is password for your CoinFLEX account found in API Details

# Authentication
auth = str(args.id) + "/" + args.cookie
string = auth + ':' + args.phrase
bytes = base64.b64encode(string.encode())
auth = bytes.decode()
headers = {'authorization': 'Basic ' + auth, 'Content-type': 'application/x-www-form-urlencoded'}

# Example REST API calls
# GET current open orders
response = requests.get(args.url + "/orders/", headers=headers)
print(response.json())

# Cancel ALL current open orders
response = requests.delete(args.url + "/orders/", headers=headers)
print(response.json())

# GET markets reference information
response = requests.get(args.url + "/markets/", headers=headers)
print(response.json())

# GET tickers 
response = requests.get(args.url + "/tickers/", headers=headers)
print(response.json())

# Example REST API calls where authentication is required
response = requests.get(args.url + "/balances/", headers=headers)
print(response.json())

# Authenticated GET API call with input parameters
previous_24h = (time.time() - 24 * 60 * 60) * 1000000
params = 'since=' + str(int(previous_24h)) + '&sort=desc&limit=10'
response = requests.get(args.url + "/trades/?" + params, headers=headers)
print(response.json())

# Authenticated POST API with input parameters
payload = {'offer_id': 1234, 'amount':5678}
response = requests.post(args.url + "/borrower/loans/", data=payload, headers=headers)
print(response.json())
