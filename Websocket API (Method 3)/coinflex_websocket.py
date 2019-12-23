import websocket
import threading
import traceback
from time import sleep
import json
import random
import logging
import requests
import time
import ssl
import base64
from ecdsa import ellipticcurve
from ecdsa import curves
from ecdsa import SigningKey
from hashlib import sha224

Assets = {}
Scales = {}

# Get the available assets and their scale up factors from the url
response = requests.get("https://webapi.coinflex.com/assets/")
asset_list = response.json()
for item in asset_list:
    Assets[item["name"]] = item["id"]
    Scales[item["name"]] = item["scale"]

class CoinFLEXWebsocket:

    secp224k1_instance = None

    OrdersChange_method = ['OrderOpened', 'OrderModified', 'OrdersMatched', 'OrderClosed', 'TickerChanged']

    def __init__(self, endpoint, base, counter, user_id=None, cookie=None, passphrase=None,
                 rest_endpoint='https://webapi.coinflex.com',socket_timeout = 5):
        '''Connect to the websocket and initialize data stores.'''
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing WebSocket.")

        self.endpoint = endpoint
        if base is None:
            raise ValueError('base id is required')
        if counter is None:
            raise ValueError('counter id is required')
        self.base = base
        self.counter = counter

        self.user_id = user_id
        self.cookie = cookie
        self.passphrase = passphrase.encode() if passphrase is not None else None

        self.rawData = {}
        self.data = {}
        self.keys = {}
        self.exited = False
        self.auth_complete = False
        self.auth_okay = False
        self.auth_tag = random.randint(0, 2 ** 63 - 1)
        self.server_nonce   = None
        self.data['PlaceOrder'] = {}
        self.data['CancelOrder'] = {}
        self.data['CancelAllOrders'] = {}
        self.data['GetTradeVolume'] = {}

        self.rest_endpoint = rest_endpoint
        auth = str(user_id) + "/" + cookie
        auth_string = auth + ':' + passphrase
        auth_bytes = base64.b64encode(auth_string.encode())
        auth = auth_bytes.decode()
        self.rest_api_headers = {'authorization': 'Basic ' + auth, 'Content-type': 'application/x-www-form-urlencoded'}

        self.socket_timeout = socket_timeout
        self.insecure_ssl = False
        self.conditional = threading.Condition()

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        self.logger.info("Connecting to %s" % endpoint)
        self.__connect(endpoint)
        self.logger.info('Connected to WS.')

        # subscribe to "WatchOrders" to listen on the realtime order book changes
        self.tags = dict(WatchOrders = random.randint(0, 2**63-1))
        self.__send_command(
            dict(
                tag=self.tags['WatchOrders'],
                method="WatchOrders",
                base=self.base,
                counter=self.counter,
                watch=True
            )
        )

        # subscribe to "WatchTicker" to listen on the realtime ticker changes
        self.tags['WatchTicker'] = random.randint(0, 2**63-1)
        self.__send_command(
            dict(
                tag=self.tags['WatchTicker'],
                method="WatchTicker",
                base=self.base,
                counter=self.counter,
                watch=True
            )
        )

    # encryption method
    @classmethod
    def secp224k1(klass):
        if klass.secp224k1_instance is None:
            _a = 0x0000000000000000000000000000000000000000000000000000000000
            _b = 0x0000000000000000000000000000000000000000000000000000000005
            _p = 0x00fffffffffffffffffffffffffffffffffffffffffffffffeffffe56d
            _Gx = 0x00a1455b334df099df30fc28a169a467e9e47075a90f7e650eb6b7a45c
            _Gy = 0x007e089fed7fba344282cafbd6f7e319f7c0b0bd59e2ca4bdb556d61a5
            _r = 0x010000000000000000000000000001dce8d2ec6184caf0a971769fb1f7

            curve_secp224k1 = ellipticcurve.CurveFp(_p, _a, _b)
            generator_secp224k1 = ellipticcurve.Point(curve_secp224k1, _Gx, _Gy, _r)

            klass.secp224k1_instance = curves.Curve(
                "SECP224k1",
                curve_secp224k1,
                generator_secp224k1,
                (1, 3, 132, 0, 20),
                "secp256k1"
            )

        return klass.secp224k1_instance

    def exit(self):
        '''Call this to exit - will close websocket.'''
        self.exited = True
        self.ws.close()

    def get_instrument(self):
        '''Call this to get the subscribed instruments'''
        instrument_dict = {v: k for k, v in Assets.items()}
        instrument = {"base": instrument_dict[self.base], "counter": instrument_dict[self.counter]}
        return instrument

    def get_ticker(self):
        '''Call this to get the most updated ticker's market status'''
        try:
            self._timed_wait(
                lambda: "ticker" in self.data.keys()
            )
            return self.data['ticker']
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for tickers")

    def funds(self):
        '''Get your margin details.'''
        response = requests.get(self.rest_endpoint + "/borrower/margin_ratios/", headers=self.rest_api_headers)
        self.data['margin'] = response.json()
        return self.data['margin']

    def positions(self, **data):
        '''Get your positions.'''
        data["method"] = "GetBalances"
        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: "balances" in self.rawData.keys()
            )
            return self.data['balances']
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for positions")

    def market_depth(self):
        '''Get market depth (orderbook). Returns all levels.'''
        return self.data['orderBook']

    def open_orders(self, **data):
        '''Get all your open orders.'''
        data["method"] = "GetOrders"

        if 'tag' not in data.keys():
            self.tags['GetOrders'] = random.randint(0, 2**63-1)
        else:
            self.tags['GetOrders'] = data['tag']
        data["tag"] = self.tags['GetOrders']

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: "order" in self.data.keys()
            )
            return self.data['order']
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for positions")

    def recent_trades(self):
        '''Get recent trades.'''
        # only rest api method can retrieve recent trades
        response = requests.get(self.rest_endpoint + "/trades/", headers=self.rest_api_headers)
        self.data['trade'] = response.json()
        return self.data['trade']

    def estimate_market_order(self, **data):
        '''Estimate Market Order'''
        data["method"] = "EstimateMarketOrder"

        if 'tag' not in data.keys():
            self.tags['EstimateMarketOrder'] = random.randint(0, 2**63-1)
        else:
            self.tags['EstimateMarketOrder'] = data['tag']
        data["tag"] = self.tags['EstimateMarketOrder']

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: "EstimateMarketOrder" in self.data.keys()
            )
            return self.data['order']
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for EstimateMarketOrder")

    def place_order(self, **data):
        '''Place Limit Order'''
        data["method"] = "PlaceOrder"

        if 'tag' not in data.keys():
            self.tags['PlaceOrder'] = random.randint(0, 2**63-1)
        else:
            self.tags['PlaceOrder'] = data['tag']
        data["tag"] = self.tags['PlaceOrder']

        # check if user want to place orders of other assets
        if 'base' not in data.keys():
            data['base'] = self.base
        if 'counter' not in data.keys():
            data['counter'] = self.counter

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: data['tag'] in self.data['PlaceOrder'].keys()
            )
            return self.data['PlaceOrder'][data['tag']]
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for PlaceOrder")

    # send cancel order with the order id
    def cancel_order(self, **data):
        '''Cancel a Single Order'''
        data["method"] = "CancelOrder"

        if 'tag' not in data.keys():
            self.tags['CancelOrder'] = random.randint(0, 2**63-1)
        else:
            self.tags['CancelOrder'] = data['tag']
        data["tag"] = self.tags['CancelOrder']

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: data['tag'] in self.data['CancelOrder'].keys()
            )
            return self.data['CancelOrder'][data['tag']]
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for CancelOrder")

    def cancel_all_orders(self, **data):
        '''Cancel all Orders'''
        data["method"] = "CancelAllOrders"

        if 'tag' not in data.keys():
            self.tags['CancelAllOrders'] = random.randint(0, 2**63-1)
        else:
            self.tags['CancelAllOrders'] = data['tag']
        data["tag"] = self.tags['CancelAllOrders']

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: data['tag'] in self.data['CancelAllOrders'].keys()
            )
            return self.data['CancelAllOrders'][data['tag']]
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for CancelAllOrders")

    def get_trade_volume(self, **data):
        '''Retrieves the 30-day trailing trade volume for the authenticated user.'''
        data["method"] = "GetTradeVolume"

        if 'tag' not in data.keys():
            self.tags['GetTradeVolume'] = random.randint(0, 2**63-1)
        else:
            self.tags['GetTradeVolume'] = data['tag']
        data["tag"] = self.tags['GetTradeVolume']

        self.__send_command(data)
        try:
            self._timed_wait(
                lambda: data['tag'] in self.data['GetTradeVolume'].keys()
            )
            return self.data['GetTradeVolume'][data['tag']]
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for GetTradeVolume")

    #
    # End Public Methods
    #

    def __connect(self, endpoint):
        '''Connect to the websocket in a thread.'''
        self.logger.debug("Starting thread")

        options = {
            "ping_interval": 45,
            "ping_timeout": self.socket_timeout
        }

        if self.insecure_ssl:
            options["sslopt"] = {"cert_reqs": ssl.CERT_NONE}

        self.ws = websocket.WebSocketApp(endpoint,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error
                                         )

        self.wst = threading.Thread(target=lambda: self.ws.run_forever(**options))
        self.wst.daemon = True
        self.wst.start()
        self.logger.debug("Started thread")

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            raise websocket.WebSocketTimeoutException('Couldn\'t connect to WS! Exiting.')

    def __get_auth(self):
        '''Authenticate the user'''
        if self.auth_complete:
            return

        if self.user_id is None or self.cookie is None or self.passphrase is None:
            self.logger.error("Missing authentication data")
            return

        self._wait_for_server_nonce()
        if self.server_nonce is None:
            self.logger.error("Server nonce not received before timeout")

        else:
            signature = self._compute_ecdsa_signature()
            self.__send_command(
                    dict(method = "Authenticate",
                    tag = self.auth_tag,
                    user_id = self.user_id,
                    cookie = self.cookie,
                    nonce = base64.b64encode(self.client_nonce).decode(),
                    signature = signature)
                )

            self._wait_for_auth_response()
            if not self.auth_complete:
                self.logger.error("Unable to complete authentication")
            elif not self.auth_okay:
                self.logger.error("Authentication failed")

    def __send_command(self, command):
        '''Send a raw command.'''

        if self._needs_authentication(command["method"]):
            self.__get_auth()
        self.ws.send(json.dumps(command))

    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        # trigger authentication
        if not self.auth_complete:
            welcome_message = json.loads(message)

            # check if the message contain the welcome message
            if welcome_message.get("notice", "") == "Welcome":
                self._process_welcome_message(welcome_message)
            # check if the authentication is successful
            elif "tag" in welcome_message and welcome_message["tag"] == self.auth_tag:
                self._process_authentication_response(welcome_message)

        try:

            data = json.loads(message)
            self.rawData = data

            # process the message if it contains 'tag'
            if "tag" in data.keys():
                if data['tag'] == self.tags['WatchOrders']:
                    self.data['orderBook'] = data['orders']
                elif data['tag'] == self.tags['WatchTicker']:
                    ticker = data.copy()
                    ticker.pop('tag')
                    ticker.pop('error_code')
                    self.data['ticker'] = ticker
                elif 'GetOrders' in self.tags.keys():
                    if data['tag'] == self.tags['GetOrders']:
                        self.data['order'] = data['orders']
                elif 'EstimateMarketOrder' in self.tags.keys():
                    if data['tag'] == self.tags['EstimateMarketOrder']:
                        order = data.copy()
                        order.pop('tag')
                        order.pop('error_code')
                        self.data['EstimateMarketOrder'] = order
                elif 'PlaceOrder' in self.tags.keys():
                    if data['tag'] == self.tags['PlaceOrder']:
                        order = data.copy()
                        self.data['PlaceOrder'][order['tag']] = order
                elif 'CancelOrder' in self.tags.keys():
                    if data['tag'] == self.tags['CancelOrder']:
                        order = data.copy()
                        self.data['CancelOrder'][order['tag']] = order
                elif 'CancelAllOrders' in self.tags.keys():
                    if data['tag'] == self.tags['CancelAllOrders']:
                        order = data.copy()
                        self.data['CancelAllOrders'][order['tag']] = order
                elif 'GetTradeVolume' in self.tags.keys():
                    if data['tag'] == self.tags['GetTradeVolume']:
                        vol = data.copy()
                        vol.pop('tag')
                        self.data['GetTradeVolume'][data['tag']] = vol

            # process the message if it contains 'balances'
            # the message is the response from the GetBalances method
            if 'balances' in data.keys():
                self.data['balances'] = data

            # Construct order book
            if ("base" in data.keys()) and ("counter" in data.keys()) and ("notice" in data.keys()):
                # Check if the response are containing the data of the right assets
                # and also from a legitimate notice
                if (data['base'] == self.base) \
                        and (data['counter'] == self.counter) \
                        and (data['notice'] in self.OrdersChange_method):
                    # Modify the order book's order entry if it is an 'OrderModified' method
                    if data['notice'] == 'OrderModified':
                        for n, i in enumerate(self.data['orderBook']):
                            if i['id'] == data['id']:
                                self.data['orderBook'][n]['quantity'] = data['quantity']
                                self.data['orderBook'][n]['price'] = data['price']
                                self.data['orderBook'][n]['time'] = data['time']
                                break
                    # Insert new order to the order book instance if it is 'OrderOpened'
                    elif data['notice'] == 'OrderOpened':
                        self.data['orderBook'] += [{"id":data['id'],"price":data['price'],"quantity":data['quantity'],"time":data['quantity']}]
                    # Delete the order from the order book instance if it is an 'OrderClosed'
                    elif data['notice'] == 'OrderClosed':
                        for n, i in enumerate(self.data['orderBook']):
                            if i['id'] == data['id']:
                                del self.data['orderBook'][n]
                                break
                    # Modify or delete order entry(s) if there is an 'OrdersMatched'
                    elif data['notice'] == 'OrdersMatched':
                        bid = data['bid'] if 'bid' in data.keys() else None
                        ask = data['bid'] if 'bid' in data.keys() else None
                        bid_ch = True if bid is None else False
                        ask_ch = True if ask is None else False

                        # Modify or delete the order according to their id,
                        # after locating them in the order book instance
                        for n, i in enumerate(self.data['orderBook']):
                            # change the bid order if possible
                            if (bid is not None) and (not bid_ch):
                                if i['id'] == bid:
                                    if data["bid_rem"] == 0:
                                        del self.data['orderBook'][n]
                                    else:
                                        self.data['orderBook'][n]['quantity'] = data['bid_rem']
                                        self.data['orderBook'][n]['time'] = data['time']
                                    bid_ch = True
                                    continue
                            # change the ask order if possible
                            if (ask is not None) and (not ask_ch):
                                if i['id'] == ask:
                                    if data["ask_rem"] == 0:
                                        del self.data['orderBook'][n]
                                    else:
                                        self.data['orderBook'][n]['quantity'] = data['ask_rem']
                                        self.data['orderBook'][n]['time'] = data['time']
                                    ask_ch = True
                                    continue
                            if bid_ch and ask_ch:
                                break
                    # if it is 'TickerChanged' from 'WatchTicker' method,
                    # update the 'ticker' instance
                    elif data['notice'] == 'TickerChanged':
                        ticker = data.copy()
                        ticker.pop('notice')
                        self.data['ticker'].update(ticker)
                        self.data['ticker']['mid'] = (float(self.data['ticker']['bid'] or 0) + float(self.data['ticker']['ask'] or 0)) / 2

                self.logger.debug(json.dumps(message))

        except:
            self.logger.error(traceback.format_exc())

    def __on_error(self, error):
        '''Called on fatal websocket errors. We exit on these.'''
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def __on_open(self, ws):
        '''Called when the WS opens.'''
        self.logger.debug("Websocket Opened.")

    def __on_close(self):
        '''Called on websocket close.'''
        self.logger.info('Websocket Closed')

    def _timed_wait(self, predicate):
        '''This function is called when the ws instance needs to wait for specific response to procceed'''
        # the waiting time is by defaul the ws timeout time
        # predicate is a boolean function to determine if the function can proceed further

        time_left = self.socket_timeout
        deadline = time.time() + time_left
        try:
            self.conditional.acquire()
            while not predicate() and time_left > 0:
                self.conditional.wait(time_left)
                time_left = deadline - time.time()
        finally:
            self.conditional.release()

    def _process_welcome_message(self, body):
        '''Process the welcome message'''
        if "nonce" not in body:
            self.logger.error("Invalid 'Welcome' message received")
        elif self.server_nonce is not None:
            self.logger.error("Server nonce received more than once")
        else:
            try:
                self.conditional.acquire()
                self.server_nonce = base64.b64decode(body["nonce"])
            except TypeError:
                self.logger.error("Server nonce received is invalid")
            finally:
                self.conditional.notify_all()
                self.conditional.release()

    def _process_authentication_response(self, body):
        '''Process the response after authentication request'''
        self.conditional.acquire()
        if body.get("error_code", -1) == 0:
            self.auth_okay = True
        else:
            self.auth_okay = False
        self.auth_complete = True
        self.conditional.notifyAll()
        self.conditional.release()

    def _wait_for_server_nonce(self):
        try:
            self._timed_wait(
                    lambda: self.server_nonce is not None
                )
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for server nonce")

    def _compute_ecdsa_signature(self):
        try:
            sys_random = random.SystemRandom()
            ecdsa_nonce = sys_random.getrandbits(224)
            self.client_nonce = random.getrandbits(16 * 8).to_bytes(16, "big")

            user_bytes = int(self.user_id).to_bytes(8, "big")

            message = b"".join([user_bytes, self.server_nonce, self.client_nonce])

            key = b"".join([user_bytes, self.passphrase])
            key_hash = sha224(key).digest()
            exponent = int.from_bytes(key_hash, "big", signed = False)

            secp224k1 = self.secp224k1()
            priv_key = SigningKey.from_secret_exponent(exponent, curve = secp224k1, hashfunc = sha224)

            r, s = priv_key.sign_deterministic(message, hashfunc = sha224,
                    sigencode = lambda r, s, order: (r, s)
                )
            r = r.to_bytes(28, "big")
            s = s.to_bytes(28, "big")
            r = base64.b64encode(r).decode()
            s = base64.b64encode(s).decode()

            return r, s

        except ValueError:
            self._err_handler(self, "Invalid signature data")

    def _wait_for_auth_response(self):
        try:
            self._timed_wait(
                    lambda: self.auth_complete is True
                )
        except KeyboardInterrupt:
            self.logger.error("Interrupted while waiting for authentication to complete")

    def _needs_authentication(self, method_name):
        return method_name not in [
                "Authenticate",
                "EstimateMarketOrder",
                "WatchOrders",
                "WatchTicker"
            ]
