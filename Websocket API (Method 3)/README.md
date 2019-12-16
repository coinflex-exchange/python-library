# CoinFLEX Python Websocket Client - Method 3
An Python class, together with a "driver" code, meant as an example of making authenticated calls to CoinFLEX's [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md).

## Prerequisites
* [Python 3](https://www.python.org/) interpreter, together with the "devel" counterpart
* [gmp](https://gmplib.org/) GNU Multi Precision Arithmetic Library, together with the "devel" counterpart
* [pip3](https://pip.pypa.io/en/stable/) package manager
* [ecdsa](https://pypi.org/project/ecdsa/) library for creating Elliptic Curve signatures
* [websocket-client](https://pypi.org/project/websocket-client/) library for WebSocket support

## Preparation
In major Linux distributions, packages `Python 3` and `pip3` either are already installed, or can be installed using the distribution-specific package manager.
Package `pip` works **only** with `Python 2`, to install pip packages for `Python 3`, `pip3` tool needs to be used.
On Windows, `pip3` package manager comes installed as a part of the standard `Python 3` [release.](https://www.python.org/downloads/windows/)
The client also imports the following: `base64`, `hashlib`, `json`, `random`, `ssl`, `threading`, `time`. All of these; however, come together with a `Python 3` installation, and are merely enumerated here.

To install `websocket-client` and `ecdsa` libraries, run
```
pip3 install [--user] "websocket-client<0.49.0" ecdsa
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

There are couples of methods in the client related to our API, including
```
get_instrument
get_ticker
funds
positions
market_depth
open_orders
recent_trades
estimate_market_order
place_order
cancel_order
cancel_all_orders
get_trade_volume
```

The connection is made as soon as the client is initiated, and meanwhile subscribing to the realtime data for the ticker. The authentication data are sent the first time non-public method is being called.

The client also defines an `Assets` dictionary, which contains mappings between asset names and their codes.
