# CoinFLEX Python API Clients
CoinFLEX's application programming interfaces [API](https://github.com/coinflex-exchange/API) provide our clients programmatic access to control aspects of their accounts and to place orders on CoinFLEX's trading platforms. 

CoinFLEX provides several different types of APIs:

* our native [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md)
* a [REST API](https://github.com/coinflex-exchange/API/blob/master/REST.md)
* an [Event Stream resource](https://github.com/coinflex-exchange/API/blob/master/EventStream.md) 
* and a second futures [Event Stream resource](https://github.com/coinflex-exchange/API/blob/master/FUTURES.md#get-borrowerevents) for your collateral, leverage and margin

Using these interfaces it is possible to make both authenticated and unauthenticated API calls, with the exception of the Futures Event Stream which is authenticated only.

Here we provide examples of how to connect to each of these APIs using Python.

## Websocket API Client
Its worth mentioning that there are several different apporaches to creating a Python Websocket client with different examples submitted here to help clients get connected.

* Method 1 - Uses [websocket-client][ws-client]
* Method 2 - Uses [asyncio][asyncio] in conjunction with [websockets][websockets]

[ws-client]:https://pypi.org/project/websocket-client/
[websockets]:https://pypi.org/project/websockets/
[asyncio]:https://pypi.org/project/asyncio/
[sse-client]:https://pypi.org/project/aiohttp-sse-client/
[cflex-ws-method2]:https://github.com/coinflex-exchange/python-library/tree/master/Websocket%20API%20(Method%202)

## Event Stream API
Current example shown here uses [aiohttp-sse-client][sse-client], primarily because it has full asyncio support meaning this approach can be combined with [Websocket - Method 2][cflex-ws-method2] allowing clients to maintain two CoinFLEX data streams in parrallel, (1) from an Event Stream and (2) from a websocket.
