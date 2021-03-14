#!/bin/python

import tempfile
import argparse
import sys

from urllib.parse import urljoin
from pathlib import Path, PurePath
from crypto_common import RatesCache
from decimal import *

cache_directory = PurePath(tempfile.gettempdir(), 'py_crypto/shakepay')
quote_filename = cache_directory / 'quote.json'

shakepay_base_endpoint = "https://api.shakepay.com"
quote_endpoint         = urljoin(shakepay_base_endpoint, '/quote?includeFees=true')

cache_expiry_in_seconds = 5

class ShakepayServie:
    base_asset_dict = None
    ticker_set = None
    
    def __init__(self):
        self.rates_cache = RatesCache(quote_endpoint,
                                      cache_expiry_in_seconds,
                                      self.load_json_response,
                                      cache_directory,
                                      quote_filename)
        
    def find_price(self, base_asset, quote_asset, buy):
        self.rates_cache.get_prices()
        
        divide = False
        if buy:
            from_asset = quote_asset.lower()
            to_asset = base_asset.lower()
            divide = True
        else:
            from_asset = base_asset.lower()
            to_asset = quote_asset.lower()
            
        price = None
        if from_asset in self.base_asset_dict and to_asset in self.base_asset_dict[from_asset]:
            price = Decimal(self.base_asset_dict[from_asset][to_asset]['rate'])
            if divide:
                price = Decimal(1) / price
        return price
        
    def load_json_response(self, response):
        self.base_asset_dict = dict()
        self.ticker_set = set()
        
        for item in response:
            if 'timestamp' in item:
                continue
            tickers = item['symbol'].split('_')
            if len(tickers) != 2:
                sys.quit('Invalid symbol {0}'.format(item['symbol']))
                
            base_asset = tickers[0].lower()
            quote_asset = tickers[1].lower()
            
            self.ticker_set.add(base_asset)
            self.ticker_set.add(quote_asset)
            
            self.base_asset_dict.setdefault(base_asset, dict()).update({quote_asset : item})
            
def show_result(amount, base_asset):
    base_asset = base_asset.lower()
    quote_asset = args.quote_asset
    if quote_asset is None:
        quote_asset = 'btc' if base_asset == 'cad' else 'cad'
    price = shakepay.find_price(base_asset, quote_asset, not args.sell)
    print(amount * price, quote_asset.upper())
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sell", action="store_true", default=False, help="The side of order is sell. By default it's --buy")
    parser.add_argument("-b", "--buy", action="store_true", help="The side of order is buy. By default it's --buy")
    parser.add_argument("-q", "--quote-asset", dest="quote_asset", help="The quote asset. If base-asset is CAD, by default it's BTC; otherwise it's CAD")
    parser.add_argument("amount", nargs='?', default=None, type=Decimal, help="The amount of crypto currency")
    parser.add_argument("base_asset", nargs='?', default=None, help="The base asset.")
    
    global args
    args = parser.parse_args()
    
    if args.sell and args.buy:
        sys.exit('You can use --sell and --buy together')
        
    global shakepay
    shakepay = ShakepayServie()
    # If amount and base asset is not in argument list, we read them from input. By doing that we can pipe into this script
    # For example echo "0.0005 btc" | shakepay.py
    if args.amount is None or args.base_asset is None:
        for line in sys.stdin:
            tokens = line.split()
            amount = Decimal(tokens[0])
            base_asset = tokens[1]
            show_result(amount, base_asset)
    else:
        show_result(args.amount, args.base_asset)
    
if __name__ == "__main__":
    main()
