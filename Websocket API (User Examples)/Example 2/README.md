# CoinFLEX Python Websocket Client - Method 3
An Python class, together with a "driver" code, meant as an example of making authenticated calls to CoinFLEX's [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md).

## Prerequisites
* [Python 3](https://www.python.org/) interpreter, together with the "devel" counterpart
* [gmp](https://gmplib.org/) GNU Multi Precision Arithmetic Library, together with the "devel" counterpart
* [pip3](https://pip.pypa.io/en/stable/) package manager
* [ecdsa](https://pypi.org/project/ecdsa/) library for creating Elliptic Curve signatures
* [websockets](https://websockets.readthedocs.io/) library for WebSocket support
* [requests](https://pypi.org/project/requests/) library for HTTP requests

## Preparation
In major Linux distributions, packages `Python 3` and `pip3` either are already installed, or can be installed using the distribution-specific package manager.
Package `pip` works **only** with `Python 2`, to install pip packages for `Python 3`, `pip3` tool needs to be used.
On Windows, `pip3` package manager comes installed as a part of the standard `Python 3` [release.](https://www.python.org/downloads/windows/)
The client also imports the following: `base64`, `hashlib`, `json`, `random`, `asyncio`, `time`. All of these; however, come together with a `Python 3` installation, and are merely enumerated here.

To install `websockets`, `ecdsa`, `requests` libraries, run
```
pip3 install [--user] websockets ecdsa requests
```
with appropriate privileges.

After the above dependencies have been met, the client is ready to run.

## Executing
Fill out the arguments in the `request: dict` to request for available methods on [WebSocket API](https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md). If authentication is necessary, the class `args` has to be filled out before starting the program. The program can only send one request per execution.

## Details
The main part of the client is a `subscribe` function, in which a class of authentication details and a `dict` of request are the necessary arguments. Some other functions, `authenticate`, `secp224k1` and `compute_ecdsa_signature` are incorporated inside for the authenticating process, while `get_assets` and `get_markets` defines an `Assets` and `Markets` dictionary, which contains mappings between asset names and their codes.

The class `args` which contains authentication details include the following elements:

| Name | Descriptions |
| --- | --- |
| `auth` | boolean that decides whether authentication is proccessed |
Below are only needed if auth == True
| `tag` | an integer echoes in the reply of authentication |
| `url` | the url of the endpoint (you can switch between live and stage environment) |
| `cookie` | the base64-encoded login cookie which is unique to the specified user |
| `id` | the numeric identifier of the user  |
| `phrase` | the passphrase of the user |


