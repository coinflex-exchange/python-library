import requests
import base64
import time

class args:
    url="https://webapi.coinflex.com"       #change URL between STAGE and LIVE
    cookie=''                                     #this is the API key from your CoinFLEX account found in API Details
    id=''                                         #this is user ID for your CoinFLEX account found in API Details
    phrase=''                                     #this is password for your CoinFLEX account found in API Details
    
#Authentication
string=str(args.id)+"/"+args.cookie+':'+args.phrase
bytes=base64.b64encode(string.encode())
auth=bytes.decode()
headers = {'authorization': 'Basic ' + auth, 'Content-type': 'application/x-www-form-urlencoded'}

#Example REST API calls
response = requests.get(args.url+"/assets/", headers=headers)
print(response.json())

response = requests.get(args.url+"/markets/", headers=headers)
print(response.json())

response = requests.get(args.url+"/tickers/", headers=headers)
print(response.json())

#Example REST API calls where authentication is required
response = requests.get(args.url+"/balances/", headers=headers)
print(response.json())

#Authenticated REST API call with input parameters 
previous_24h=(time.time()-24*60*60)*1000000
params = 'since='+str(int(previous_24h))+'&sort=desc&limit=10'
response = requests.get(args.url+"/trades/?"+params, headers=headers)
print(response.json())
