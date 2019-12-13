import asyncio
import websockets
import base64
import random
import requests
import json
import time
from ecdsa import ellipticcurve
from ecdsa import curves
from ecdsa import SigningKey
from hashlib import sha224

class args:
    auth= False
    tag=123                                     #any integer tag which will be returned in the authentication response from the exchnage
    url="wss://api.coinflex.com/v1"             #websocket URL for LIVE
    cookie=''                                   #this is the API key from your CoinFLEX account
    id=0                                        #this is core ID for your CoinFLEX account
    phrase=''                                   #this is password for your CoinFLEX account


# Connects to the CoinFLEX /assets/ REST endpoint to retrieve the asset ID's
def get_assets():
    Assets = {}
    response= requests.get(url="https://webapi.coinflex.com/assets/",headers={'Content-type': 'application/x-www-form-urlencoded'})
    asset_list = response.json()
    for item in asset_list:
        Assets[item['name']] = {}
        Assets[item['name']]['id'] = item['id']
        Assets[item['name']]['scale'] = item['scale']        
    return Assets
Assets = get_assets()

def get_markets():
    Markets = {}
    response= requests.get(url="https://webapi.coinflex.com/markets/",headers={'Content-type': 'application/x-www-form-urlencoded'})
    market_list = response.json()
    for item in market_list:
        Markets[item['base']] = {}
        Markets[item['base']]['counter'] = item['counter']
        if item.get('start')!=None: 
            Markets[item['base']]['start'] = item['start']
        if item.get('expires')!=None: 
            Markets[item['base']]['expires'] = item['expires']
    return Markets
Markets = get_markets() 

def secp224k1():
    _a  = 0x0000000000000000000000000000000000000000000000000000000000
    _b  = 0x0000000000000000000000000000000000000000000000000000000005
    _p  = 0x00fffffffffffffffffffffffffffffffffffffffffffffffeffffe56d
    _Gx = 0x00a1455b334df099df30fc28a169a467e9e47075a90f7e650eb6b7a45c
    _Gy = 0x007e089fed7fba344282cafbd6f7e319f7c0b0bd59e2ca4bdb556d61a5
    _r  = 0x010000000000000000000000000001dce8d2ec6184caf0a971769fb1f7
    curve_secp224k1 = ellipticcurve.CurveFp(_p, _a, _b)
    generator_secp224k1 = ellipticcurve.Point(curve_secp224k1, _Gx, _Gy, _r)
    secp224k1_instance = curves.Curve(
            "SECP224k1",
            curve_secp224k1,
            generator_secp224k1,
            (1, 3, 132, 0, 20),
            "secp256k1"
        )
    return secp224k1_instance

def compute_ecdsa_signature(user_id,passphrase,server_nonce,client_nonce):
    #sys_random = random.SystemRandom()
    #ecdsa_nonce = sys_random.getrandbits(224)
    user_bytes = int(user_id).to_bytes(8, "big")
    message = b"".join([user_bytes, server_nonce, client_nonce])
    key = b"".join([user_bytes, passphrase])
    key_hash = sha224(key).digest()
    exponent = int.from_bytes(key_hash, "big", signed = False)
    #secp224k1 = secp224k1()
    priv_key = SigningKey.from_secret_exponent(exponent, curve = secp224k1(), hashfunc = sha224)
    r, s = priv_key.sign_deterministic(message, hashfunc = sha224,
            sigencode = lambda r, s, order: (r, s)
        )
    r = r.to_bytes(28, "big")
    s = s.to_bytes(28, "big")
    r = base64.b64encode(r).decode()
    s = base64.b64encode(s).decode()

    return r, s

def authenticate(tag,user_id,cookie,passphrase,server_nonce):
    client_nonce = random.getrandbits(16 * 8).to_bytes(16, "big")
    signature = compute_ecdsa_signature(user_id,passphrase.encode(),server_nonce,client_nonce)
    send_signature= {"tag":tag, "method": "Authenticate","user_id": user_id,"cookie": cookie,
                     "nonce": base64.b64encode(client_nonce).decode(),"signature": signature}
    return send_signature


async def subscribe():
    global ws
    async with websockets.connect(args.url) as ws:  
        while True:
            if not ws.open: 
                ws = await websockets.connect(args.url)
            try:
                response = await ws.recv()
                msg = json.loads(response)
                print(msg)
                #if websocket connection is successful a welomce notice and a NONCE will be returned in a repsonse from the exchange
                if 'nonce' in msg:
                    #once websocket is connected then send commands to subscribe to the public endpoints such as WatchTicker and WatchOrders
                    payload_ticker = {"method": "WatchTicker", "base": Assets['XBT']['id'],"counter": Assets['USDT']['id'], "watch": True}
                    await ws.send(json.dumps(payload_ticker))
                    
                    payload_ticker = {"method": "WatchOrders", "base": Assets['XBT']['id'],"counter": Assets['USDT']['id'], "watch": True}
                    await ws.send(json.dumps(payload_ticker))
                    
                    #If client wants to authenticate then set args.auth=True in the args class above and this will run
                    if args.auth:
                        server_nonce = base64.b64decode(msg['nonce'])
                        payload_auth = authenticate(args.tag,args.id,args.cookie,args.phrase,server_nonce)
                        await ws.send(json.dumps(payload_auth))
                
                #if the authenticate tag is returned in the repsonse then authentication was sucessful
                if 'tag' in msg and msg['tag']==args.tag:
                    print('Authentication Successful')
                    #once websocket is authenticated then send commands to subscribe to the private endpoints such as GetBalances
                    payload_balances = {"method": "GetBalances"}
                    await ws.send(json.dumps(payload_balances))
      
            except Exception as error:
                err_msg = 'Error: '+str(time.time())+' '+repr(error)
                print(err_msg)
              
asyncio.get_event_loop().run_until_complete(subscribe())
