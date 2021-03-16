#!/bin/python

import argparse
import sys

from urllib.parse import urljoin
from pathlib import Path, PurePath
from crypto_common import RatesCache, cache_directory_base
from decimal import *

newton_base_endpoint = 'https://api.newton.co'
newton_rates_endpoint = urljoin(newton_base_endpoint, '/dashboard/api/rates/')

cache_directory = cache_directory_base / 'newton'
rates_filename = cache_directory / 'rates.json'

cache_expiry_in_seconds = 5

class NewtonService:
    
    base_asset_dict = None
    quote_asset_dict = None
    ticker_set = None
    
    def __init__(self):
        self.rates_cache = RatesCache(newton_rates_endpoint,
                                      cache_expiry_in_seconds,
                                      self.load_json_response,
                                      cache_directory,
                                      rates_filename)
    
    def find_price(self, base_asset, quote_asset, buy):
        self.rates_cache.get_prices()
        
        ba = base_asset.lower()
        qa = quote_asset.lower()
        
        price = None
        if ba in self.base_asset_dict and qa in self.base_asset_dict[ba]:
            rate = self.base_asset_dict[ba][qa]
            # In Newton's perspective (maker) it's ask order, but from customer's perspective (taker) it's a buy order
            #   Newton (maker) |  Customer (taker)
            # -----------------|------------------
            #   ask btc/cad    |  bid btc/cad
            #   ask btc/cad    |  ask cad/btc
            # -----------------|------------------
            #   bid btc/cad    |  ask btc/cad
            #   bid btc/cad    |  bid cad/btc
            price = Decimal(rate['ask']) if buy else Decimal(rate['bid'])
        elif ba in self.quote_asset_dict and qa in self.quote_asset_dict[ba]:
            rate = self.quote_asset_dict[ba][qa]
            tp = Decimal(rate['bid']) if buy else Decimal(rate['ask'])
            price = Decimal(1) / tp
        return price
    
    def load_json_response(self, response):
        self.base_asset_dict = dict()
        self.quote_asset_dict = dict()
        self.ticker_set = set()
        for symbol in response["rates"]:
            rate = dict()
            #   Newton (maker) |  Customer (taker)
            # -----------------|------------------
            #   ask btc/cad    |  bid btc/cad
            #   ask btc/cad    |  ask cad/btc
            # -----------------|------------------
            #   bid btc/cad    |  ask btc/cad
            #   bid btc/cad    |  bid cad/btc
            #
            # So we use Newton perspective:
            base_asset = symbol["to"].lower() 
            quote_asset = symbol["from"].lower()
            
            self.ticker_set.add(base_asset)
            self.ticker_set.add(quote_asset)
            
            self.base_asset_dict.setdefault(base_asset, dict()).update({quote_asset : symbol})
            self.quote_asset_dict.setdefault(quote_asset, dict()).update({base_asset : symbol})

def show_result(amount, base_asset):
    base_asset = base_asset.lower()
    quote_asset = args.quote_asset
    if quote_asset is None:
        quote_asset = 'btc' if base_asset == 'cad' else 'cad'
    price = newton.find_price(base_asset, quote_asset, not args.sell)
    print(amount * price - args.network_fee, quote_asset.upper())
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sell", action="store_true", default=False, help="The side of order is sell. By default it's --buy")
    parser.add_argument("-b", "--buy", action="store_true", help="The side of order is buy. By default it's --buy")
    parser.add_argument("-q", "--quote-asset", dest="quote_asset", help="The quote asset. If base-asset is CAD, by default it's BTC; otherwise it's CAD")
    parser.add_argument("-n", "--network-fee", dest="network_fee", default=Decimal(0), type=Decimal, help="Network fee. By default it's 0")
    parser.add_argument("amount", nargs='?', default=None, type=Decimal, help="The amount of crypto currency")
    parser.add_argument("base_asset", nargs='?', default=None, help="The base asset.")
    
    global args
    args = parser.parse_args()
    
    if args.sell and args.buy:
        sys.exit('You can use --sell and --buy together')
        
    global newton
    newton = NewtonService()
    # If amount and base asset is not in argument list, we read them from input. By doing that we can pipe into this script
    # For example echo "0.0005 btc" | newton.py
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

