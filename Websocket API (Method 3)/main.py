from coinflex_websocket import CoinFLEXWebsocket, Assets
import logging
from time import sleep


# Basic use of websocket.
def run():
    logger = setup_logger()

    # Instantiating the WS will make it connect. Be sure to add your api_key/api_secret.
    ws = CoinFLEXWebsocket(endpoint="wss://api.coinflex.com/v1", base=Assets['XBTDEC'],counter=Assets['USDTDEC'], user_id=None,
                         cookie='', passphrase='')

    logger.info("Instrument data: %s" % ws.get_instrument())

    # Run forever
    while(ws.ws.sock.connected):
        logger.info("Ticker: %s" % ws.get_ticker())
        if ws.passphrase:
            logger.info("Funds: %s" % ws.funds())
            logger.info("Trade Volume: %s\n\n" % ws.get_trade_volume(asset=Assets['XBTDEC']))
            # logger.info("Place Order: %s\n\n" % ws.place_order(quantity=-10, price=75000000))

        logger.info("Market Depth: %s" % ws.market_depth())
        logger.info("Recent Trades: %s\n\n" % ws.recent_trades())
        sleep(10)


def setup_logger():
    # Prints logger info to terminal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Change this to DEBUG if you want a lot more info
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    run()
