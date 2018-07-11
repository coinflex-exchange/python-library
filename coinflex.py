import base64
import json
import random
import ssl
import threading
import time
import websocket

from fastecdsa import _ecdsa
from fastecdsa import curve
from hashlib import sha224

Assets = {
    "XBT"      : 63488,
    "BCH"      : 63496,
    "EUR"      : 64000,
    "GBP"      : 64032,
    "USD"      : 64128,
    "PLN"      : 64936,
    "XBTJAN18" : 51200,
    "USDJAN18" : 51840,
    "XBTFEB18" : 51201,
    "USDFEB18" : 51841,
    "XBTMAR18" : 51202,
    "USDMAR18" : 51842,
    "XBTAPR18" : 51203,
    "USDAPR18" : 51843,
    "XBTMAY18" : 51204,
    "USDMAY18" : 51844,
    "XBTJUN18" : 51205,
    "USDJUN18" : 51845,
    "XBTJUL18" : 51206,
    "USDJUL18" : 51846,
    "XBTAUG18" : 51207,
    "USDAUG18" : 51847,
    "XBTSEP18" : 51208,
    "USDSEP18" : 51848,
    "XBTOCT18" : 51209,
    "USDOCT18" : 51849,
    "XBTNOV18" : 51210,
    "USDNOV18" : 51850,
    "XBTDEC18" : 51211,
    "USDDEC18" : 51851
}

class WSClient(websocket.WebSocketApp):
    def __init__(self, url,
            msg_handler     = None,
            err_handler     = None,
            open_handler    = None,
            close_handler   = None,
            ping_handler    = None,
            pong_handler    = None,
            insecure_ssl    = False,
            socket_timeout  = 5
        ):

        self.auth_complete  = False
        self.auth_okay      = False
        self.auth_tag       = -1
        self.url            = url
        self.connected      = False
        self.user_id        = None
        self.cookie         = None
        self.passphrase     = None
        self.server_nonce   = None
        self.client_nonce   = None
        self.socket_timeout = socket_timeout
        self.insecure_ssl   = insecure_ssl

        self.open_handler   = open_handler
        self.msg_handler    = msg_handler
        self.err_handler    = err_handler

        self.conditional    = threading.Condition()

        websocket.WebSocketApp.__init__(
                self, self.url,
                on_message  = self._msg_handler,
                on_error    = self._err_handler,
                on_open     = self._open_handler,
                on_close    = close_handler,
                on_pong     = pong_handler,
                on_ping     = ping_handler
            )


    def _open_handler(self, ws):
        self.conditional.acquire()
        self.connected = True
        self.conditional.notifyAll()
        self.conditional.release()

        if self.open_handler is not None:
            self.open_handler(self)


    def _err_handler(self, ws, error):
        if self.err_handler is not None:
            self.err_handler(self, error)
        else:
            raise ConnectionError("Connection to %s failed: %s"%(self.url, error))


    def _msg_handler(self, ws, message):
        if not self.auth_complete:
            body = json.loads(message)
            self._body_scan(body)

        if self.msg_handler is not None:
            self.msg_handler(self, message)


    def _process_welcome_message(self, body):
        if "nonce" not in body:
            self._err_handler(self, "Invalid 'Welcome' message received")
        elif self.server_nonce is not None:
            self._err_handler(self, "Server nonce received more than once")
        else:
            try:
                self.conditional.acquire()
                self.server_nonce = base64.b64decode(body["nonce"])
            except TypeError:
                self._err_handler(self, "Server nonce received is invalid")
            finally:
                self.conditional.notify_all()
                self.conditional.release()


    def _process_authentication_response(self, body):
        self.conditional.acquire()
        if body.get("error_code", -1) == 0:
            self.auth_okay = True
        else:
            self.auth_okay = False
        self.auth_complete = True
        self.conditional.notifyAll()
        self.conditional.release()


    def _body_scan(self, body):
        if body.get("notice", "") == "Welcome":
            self._process_welcome_message(body)
        elif "tag" in body and body["tag"] == self.auth_tag:
            self._process_authentication_response(body)


    def _needs_authentication(self, method_name):
        return method_name not in [
                "Authenticate",
                "EstimateMarketOrder",
                "WatchOrders",
                "WatchTicker"
            ]


    def set_auth_data(self, user_id, cookie, passphrase):
        self.user_id = user_id
        self.cookie  = cookie
        self.passphrase = passphrase.encode()


    def send(self, json_message):
        if self._needs_authentication(json_message["method"]):
            self.authenticate()
        self._smart_connect()
        super().send(json.dumps(json_message))


    def stop(self):
        self.keep_running = False


    def _timed_wait(self, predicate):
        time_left = self.socket_timeout
        deadline = time.time() + time_left
        try:
            self.conditional.acquire()
            while not predicate() and time_left > 0:
                self.conditional.wait(time_left)
                time_left = deadline - time.time()
        finally:
            self.conditional.release()


    def _smart_connect(self):
        if self.connected:
            return
        options = {
                "ping_interval": 45,
                "ping_timeout": self.socket_timeout
            }
        if self.insecure_ssl:
            options["sslopt"] = {"cert_reqs": ssl.CERT_NONE}
        worker = threading.Thread(target = lambda:
                self.run_forever(**options)
            )
        worker.daemon = True
        worker.start()
        try:
            self._timed_wait(
                    lambda: self.connected
                )
        except KeyboardInterrupt:
            self._err_handler(self, "Interrupted while establishing the connection")


    def _wait_for_server_nonce(self):
        try:
            self._timed_wait(
                    lambda: self.server_nonce is not None
                )
        except KeyboardInterrupt:
            self._err_handler(self, "Interrupted while waiting for server nonce")


    def _wait_for_auth_response(self):
        try:
            self._timed_wait(
                    lambda: self.auth_complete is True
                )
        except KeyboardInterrupt:
            self._err_handler(self, "Interrupted while waiting for authentication to complete")


    def _compute_ecdsa_signature(self):
        try:
            sys_random = random.SystemRandom()
            ecdsa_nonce = sys_random.getrandbits(224)
            self.client_nonce = random.getrandbits(16 * 8).to_bytes(16, "big")

            user_bytes = int(self.user_id).to_bytes(8, "big")

            key = b"".join([user_bytes, self.passphrase])
            key_hash = sha224(key).digest()
            priv_key = int.from_bytes(key_hash, "big", signed = False)

            message = b"".join([user_bytes, self.server_nonce, self.client_nonce])
            message_hash = sha224(message).hexdigest()

            secp224k1 = curve.secp224k1
            r, s = _ecdsa.sign(
                    message_hash,
                    str(priv_key),
                    str(ecdsa_nonce),
                    str(secp224k1.p),
                    str(secp224k1.a),
                    str(secp224k1.b),
                    str(secp224k1.q),
                    str(secp224k1.gx),
                    str(secp224k1.gy),
                )
            r = int(r).to_bytes(28, "big")
            s = int(s).to_bytes(28, "big")
            r = base64.b64encode(r).decode()
            s = base64.b64encode(s).decode()
            return r, s

        except ValueError:
            self._err_handler(self, "Invalid signature data")


    def _send_signature(self, **sig_data):
        self.send(sig_data)


    def authenticate(self):
        if self.auth_complete:
            return

        if self.user_id is None or self.cookie is None or self.passphrase is None:
            self._err_handler(self, "Missing authentication data")
            return

        self._smart_connect()

        self._wait_for_server_nonce()
        if self.server_nonce is None:
            self._err_handler(self, "Server nonce not received before timeout")

        else:
            signature = self._compute_ecdsa_signature()
            self.auth_tag = random.randint(0, 2**63-1)
            self._send_signature(
                    method = "Authenticate",
                    tag = self.auth_tag,
                    user_id = self.user_id,
                    cookie = self.cookie,
                    nonce = base64.b64encode(self.client_nonce).decode(),
                    signature = signature
                )

            self._wait_for_auth_response()
            if not self.auth_complete:
                self._err_handler(self, "Unable to complete authentication")
            elif not self.auth_okay:
                self._err_handler(self, "Authentication failed")


    def GetBalances(self, **data):
        data["method"] = "GetBalances"
        self.send(data)


    def GetOrders(self, **data):
        data["method"] = "GetOrders"
        self.send(data)


    def EstimateMarketOrder(self, **data):
        data["method"] = "EstimateMarketOrder"
        self.send(data)


    def PlaceOrder(self, **data):
        data["method"] = "PlaceOrder"
        self.send(data)


    def CancelOrder(self, **data):
        data["method"] = "CancelOrder"
        self.send(data)


    def CancelAllOrders(self, **data):
        data["method"] = "CancelAllOrders"
        self.send(data)


    def GetTradeVolume(self, **data):
        data["method"] = "GetTradeVolume"
        self.send(data)


    def WatchOrders(self, **data):
        data["method"] = "WatchOrders"
        self.send(data)


    def WatchTicker(self, **data):
        data["method"] = "WatchTicker"
        self.send(data)

