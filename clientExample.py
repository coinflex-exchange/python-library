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


def test_drive(args):
    def print_out(ws, msg):
        print("%s: %s"%(time.time(), msg))

    coinflex= WSClient(
            args.url,
            insecure_ssl  = args.insecure,
            msg_handler   = print_out
        )

    coinflex.WatchOrders(
            base    = Assets["XBT"],
            counter = Assets["USD"],
            watch   = True
        )
    coinflex.WatchTicker(
            base    = Assets["XBT"],
            counter = Assets["USD"],
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

