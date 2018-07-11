
# CoinFLEX Python client

An Python class, together with a "driver" code, meant as an example of making authenticated calls to CoinFLEX's [WebSocket API.](https://bitbucket.org/coinflex/api/src/master/WEBSOCKET-README.md)

## Prerequisites

- [Python 3][python] interpreter
- [pip][pip] package manager
- [fastecdsa][fastecdsa] library for creating Elliptic Curve signatures

[python]:https://www.python.org/
[pip]:https://pip.pypa.io/en/stable/
[fastecdsa]:https://pypi.org/project/fastecdsa/

## Preparation

In major Linux distributions, packages `Python 3` and `pip` either are already installed, or can be installed using the distribution-specific package manager (a thing to note here is there may be two versions of the `pip` package, one for `Python 2` and `Python 3`).
Installing `fastecdsa` requires a set header files for `gmp` library, as well as a working C compiler.
In addition, the client uses the following list of imports: `base64`, `hashlib`, `json`, `random`, `sys`, `threading`, `time`, `websocket`, all of which should already be available as a part of the `Python 3` installation.
After the above dependencies have been meet, the client is ready to run.

## Executing
```shell
[<full_path>/]coinflexClient.py <WebSocket_URL>
```

In case of the missing URL, the client will report the error and exit.

## Details
The main part of the client is a `CoinflexWSS` class, which is initalised with the WebSocket endpoint's URL (obligatory) and the optional event hooks:
`msg_handler`,
`err_handler`,
`open_handler`,
`close_handler`,
`ping_handler`,
`pong_handler`,
`auth_timeout`

