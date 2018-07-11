
# CoinFLEX Python Client
An Python class, together with a "driver" code, meant as an example of making authenticated calls to CoinFLEX's [WebSocket API.](https://bitbucket.org/coinflex/api/src/master/WEBSOCKET-README.md)

## Prerequisites
- [Python 3][python] interpreter, together with the "devel" counterpart
- [gmp][gmp] GNU Multi Precision Arithmetic Library, together with the "devel" counterpart
- [pip3][pip] package manager
- [fastecdsa][fastecdsa] library for creating Elliptic Curve signatures
- [websocket-client][ws-client] library for WebSocket support

[python]:https://www.python.org/
[gmp]:https://gmplib.org/
[pip]:https://pip.pypa.io/en/stable/
[fastecdsa]:https://pypi.org/project/fastecdsa/
[ws-client]:https://pypi.org/project/websocket-client/

## Preparation
In major Linux distributions, packages `Python 3` and `pip3` either are already installed, or can be installed using the distribution-specific package manager.
Package `pip` works **only** with `Python 2`, to install prerequisites for `Python 3`, `pip3` is required.
While the client uses the following list of imports: `base64`, `hashlib`, `json`, `random`, `ssl`, `threading`, `time`, these are usually installed during `Python 3` installation.
Installing `fastecdsa` library requires `gmp` header files and a working C compiler to be present - installation details are, again, distribution-specific.

To install `websocket-client` and `fastecdsa` libraries, run
```
pip3 install websocket-client fastecdsa
```
with appropriate privileges.

After the above dependencies have been meet, the client is ready to run.

## Executing
Executing
```
[<path>/]clientExample.py -h
```
will give the list of arguments, together with their up to date description

## Details
The main part of the client is a `WSClient` class, which is initalised with the WebSocket endpoint's URL (obligatory) and the optional event hooks:
```
msg_handler
err_handler    (default action: raise a 'ConnectionError')
open_handler
close_handler
ping_handler
pong_handler
insecure_ssl
socket_timeout (default value: 5 seconds)
```

Connecting and authenticating are done in a lazy manner, i.e. the connection is being made only when data need to be sent, and authentication data are sent the first time non-public method is being called. Upon the first method being called, after the connection and/or authentication have been established, the client starts the "event" thread which monitors messages coming in from the server and handles them accordingly (which normally involves passing them to the `msg_handler`).
At the same time, the same instance of the `WSClient` class may be used to call remote WebSocket methods.
By default, **only** in two cases:

- the connection is being established, and
- the authentication is being attempted

is the `WSClient` instance thread-safe (that is, the sending thread will block and wait for the connecting/authenticating sequence to complete before allowing any further calls).

The client also defines an `Assets` dictionary, which contains mappings between asset names and their codes.
