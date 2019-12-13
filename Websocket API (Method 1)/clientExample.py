#!/usr/bin/env python3

import argparse
import os
import time

from coinflex import Assets
from coinflex import WSClient


def parse_arguments():
    parser = argparse.ArgumentParser(description = "An example Python CoinFLEX client")
    parser.add_argument(
            "url",
            help = "WebSocket endpoint, in 'ws[s]://<host>[:<port>]' format"
        )
    parser.add_argument(
            "-k", dest = "insecure", action = "store_true", default = False,
            help = "Allow insecure SSL connections"
        )
    parser.add_argument(
            "-i", type = int, metavar = "core_id", dest = "id", default = 0,
            help = "The core_id of the user"
        )
    parser.add_argument(
            "-c", metavar = "cookie", dest = "cookie", default = "",
            help = "The cookie, a.k.a API key"
        )
    passphrase = os.getenv("COINFLEX_PASSPHRASE", "")
    parser.add_argument(
            "-p", metavar = "passphrase", dest = "phrase", default = passphrase,
            help = "The passphrase. If missing, an attempt will be taken to read it from the COINFLEX_PASSPHRASE environment variable"
        )
    return parser.parse_args()


#Full list of asset string names can be found here: https://github.com/coinflex-exchange/API/blob/master/SCALE.md
def test_drive(args):
    def print_out(ws, msg):
        print("%s: %s"%(time.time(), msg))

    coinflex= WSClient(
            args.url,
            insecure_ssl  = args.insecure,
            msg_handler   = print_out
        )
    
    #Change the base and counter asset string names to point to the desired order book
    #To see all available order books please refer to the CoinFLEX /markets/ REST endpoint https://webapi.coinflex.com/markets/
    #See below for examples of subscribing to the "WatchOrders" and "WatchTicker" feed 
    #For all available commands please refer to the documentation here https://github.com/coinflex-exchange/API/blob/master/WEBSOCKET-README.md
    
    coinflex.WatchOrders(
            base    = Assets["XBT"],
            counter = Assets["USDT"],
            watch   = True
        )

    coinflex.WatchTicker(
            base    = Assets["ETHJUN"],
            counter = Assets["USDTJUN"],
            watch   = True
        )

    credentials_given = False
    if args.id > 0 and args.cookie != "" and args.phrase != "":
        coinflex.set_auth_data(args.id, args.cookie, args.phrase)
        credentials_given = True
    try:
        while True:
            time.sleep(5)
            if credentials_given:
                coinflex.GetBalances()

    except KeyboardInterrupt:
        coinflex.stop()


if __name__ == "__main__":
    args = parse_arguments()
    test_drive(args)
    
