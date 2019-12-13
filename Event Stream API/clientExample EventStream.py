import asyncio
import base64

from aiohttp_sse_client import client as sse_client

#Authentication arguments
class args:
    url="https://webapi.coinflex.com/"          #websocket URL for LIVE
    cookie=''                                   #this is the API key from your CoinFLEX account
    id=0                                        #this is core ID for your CoinFLEX account
    phrase=''                                   #this is password for your CoinFLEX account
           

#CFLEX Authentication
string=str(args.id)+"/"+args.cookie+':'+args.phrase
bytes=base64.b64encode(string.encode())
auth=bytes.decode()
headers = {'authorization': 'Basic ' + auth, 'Content-type': 'application/x-www-form-urlencoded'}

#Connects to the GET /borrower/events event stream to recieve real-time updates regarding collateral, loans and offers
async def subscribe_collateral():
    async with sse_client.EventSource(args.url+'borrower/events', headers=headers, timeout=-1) as event_source:
        try:
            async for msg in event_source:
                print(msg)

        except Exception as error:
            err_msg = repr(error)
            print(err_msg)
            pass

asyncio.get_event_loop().run_until_complete(subscribe_collateral())
