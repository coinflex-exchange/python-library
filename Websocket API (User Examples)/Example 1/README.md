# CoinFLEX Python Websocket Client - User Example 1
An Python class, together with a "driver" code, meant as an example of making authenticated calls to CoinFLEX's [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md).

## Prerequisites
* [Python 3](https://www.python.org/) interpreter, together with the "devel" counterpart
* [gmp](https://gmplib.org/) GNU Multi Precision Arithmetic Library, together with the "devel" counterpart
* [pip3](https://pip.pypa.io/en/stable/) package manager
* [ecdsa](https://pypi.org/project/ecdsa/) library for creating Elliptic Curve signatures
* [websocket-client](https://pypi.org/project/websocket-client/) library for WebSocket support
* [requests](https://pypi.org/project/requests/) library for HTTP requests

## Preparation
In major Linux distributions, packages `Python 3` and `pip3` either are already installed, or can be installed using the distribution-specific package manager.
Package `pip` works **only** with `Python 2`, to install pip packages for `Python 3`, `pip3` tool needs to be used.
On Windows, `pip3` package manager comes installed as a part of the standard `Python 3` [release.](https://www.python.org/downloads/windows/)
The client also imports the following: `base64`, `hashlib`, `json`, `random`, `ssl`, `threading`, `time`, `logging`, `traceback`. All of these; however, come together with a `Python 3` installation, and are merely enumerated here.

To install `websocket-client`, `ecdsa`, `requests` libraries, run
```
pip3 install [--user] "websocket-client<0.49.0" ecdsa requests
```
with appropriate privileges.

After the above dependencies have been met, the client is ready to run.

## Executing
Input the credentials of your account in `main.py` (if needed), together with the methods you hope to run.
Executing
```
[<path>/]main.py
```
will output the websocket messages and other debug info.

## Details
The main part of the client is a `CoinFLEXWebsocket` class, which is initalised with the WebSocket endpoint's URL, the ticker you want to subscribe to, and the optional user credentials (user id, api cookie and the passphrase of your account).

The connection is made as soon as the client is initiated, and meanwhile subscribing to the realtime data for the ticker. The authentication data are sent the first time non-public method is being called. For those client's fucntions referenced to the methods in our API, some arguments have to be customised and input before called. For example, when calling the `cancel_order` function, a method of `CancelOrder` will be invoked at the endpoint, in which `id` is obligatory while others are left optional.

The table below shows client's functions and their corresponding API methons which can take extra arguments. For more details please check out CoinFLEX's [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md).

| Client's Function | API Method Name | Functionality |
| --- | --- | --- |
| `positions` | GetBalances | retrieve the balances of the account |
| `open_orders` | GetOrders | retrieve all the open orders of the account |
| `estimate_market_order` | EstimateMarketOrder | returns the quantity that would have been traded if a market order were made |
| `place_order` | PlaceOrder | place a limit order |
| `cancel_order` | CancelOrder | cancel a order |
| `cancel_all_orders` | CancelAllOrders | cancell all open orders |
| `get_trade_volume` | GetTradeVolume | retrieve the 30-day trailing trade volume for the account |
| `get_instrument` | -- | return the ticker that is currently subscribed to |
| `get_ticker` | -- | return the current ticker's market prices and volume |
| `funds` | -- | retrieve the account's margin details |
| `market_depth` | -- | return the order book of the ticker |
| `recent_trades` | -- | return recent trades of the account |


The `main.py` lists out some examples of the usage of those functions.

The client also defines an `Assets` dictionary, which contains mappings between asset names and their codes.
