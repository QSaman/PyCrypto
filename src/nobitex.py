#!/bin/python

import tempfile
import sys
import argparse

from urllib.parse import urljoin
from pathlib import Path, PurePath
from crypto_common import RatesCache
from decimal import *

nobitex_base_endpoint = 'https://api.nobitex.ir'
nobitex_market_endpoint = urljoin(nobitex_base_endpoint, '/market/stats?srcCurrency=btc,eth,ltc,usdt,xrp,bch,bnb,eos,xlm,etc,trx,doge,pmn&dstCurrency=rls,usdt')

cache_directory = PurePath(tempfile.gettempdir(), 'py_crypto/nobitex')
market_filename = cache_directory / 'market.json'

cache_expiry_in_seconds = 5

class NobitexService:
    def __init__(self):
        self.rates_cache = RatesCache(nobitex_market_endpoint,
                                      cache_expiry_in_seconds,
                                      self.load_json_response,
                                      cache_directory,
                                      market_filename)

    def find_price(self, base_asset, quote_asset, buy):
        self.rates_cache.get_prices()
        
        ba = base_asset.lower()
        qa = quote_asset.lower()
        
        price = None
        if ba in self.base_asset_dict and qa in self.base_asset_dict[ba]:
            rate = self.base_asset_dict[ba][qa]
            price = Decimal(rate['bestSell']) if buy else Decimal(rate['bestBuy'])
        elif ba in self.quote_asset_dict and qa in self.quote_asset_dict[ba]:
            rate = self.quote_asset_dict[ba][qa]
            tp = Decimal(rate['bestBuy']) if buy else Decimal(rate['bestSell'])
            price = Decimal(1) / tp
        return price
        
    def load_json_response(self, response): 
        self.base_asset_dict = dict()
        self.quote_asset_dict = dict()
        self.ticker_set = set()
        
        def correct_symbol(asset):
            #The official symbol is IRR not RLS!
            if asset.lower() == "rls":
                return "irr"
            return asset
        
        for key, value in response['stats'].items():
            tickers = key.split('-')
            if len(tickers) != 2:
                sys.quit("Invalid symbol ", key)
            base_asset = correct_symbol(tickers[0].lower())
            quote_asset = correct_symbol(tickers[1].lower())
            
            self.ticker_set.add(base_asset)
            self.ticker_set.add(quote_asset)
            
            self.base_asset_dict.setdefault(base_asset, dict()).update({quote_asset : value})
            self.quote_asset_dict.setdefault(quote_asset, dict()).update({base_asset : value})
        
def show_result(amount, base_asset):
    base_asset = base_asset.lower()
    quote_asset = args.quote_asset
    if base_asset == "irt":
        base_asset = "irr"
        amount = amount * 10
    if quote_asset is None:
        quote_asset = 'btc' if base_asset == 'irr' else 'irt'
        
    convert_quote_to_tomans = False
    if quote_asset == "irt":
        quote_asset = "irr"
        convert_quote_to_tomans = True
    price = nobitex.find_price(base_asset, quote_asset, not args.sell)
    
    if convert_quote_to_tomans:
        price = price / Decimal(10)
        quote_asset = "irt"
    
    print(amount * price * (Decimal(1) - args.trading_fee / Decimal(100)), quote_asset)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sell", action="store_true", default=False, help="The side of order is sell. By default it's --buy")
    parser.add_argument("-b", "--buy", action="store_true", help="The side of order is buy. By default it's --buy")
    parser.add_argument("-q", "--quote-asset", dest="quote_asset", help="The quote asset. If base-asset is IRR or IRT, by default it's BTC; otherwise it's IRT")
    parser.add_argument("-f", "--trading-fee", dest="trading_fee", default=Decimal(0.35), type=Decimal, help="Trading fees in percentage. By default it's 0.35")
    parser.add_argument("amount", nargs='?', default=None, type=Decimal, help="The amount of crypto currency")
    parser.add_argument("base_asset", nargs='?', default=None, help="The base asset.")
    
    global args
    args = parser.parse_args()
    
    if args.sell and args.buy:
        sys.exit('You can use --sell and --buy together')
        
    global nobitex
    nobitex = NobitexService()
    # If amount and base asset is not in argument list, we read them from input. By doing that we can pipe into this script
    # For example echo "0.0005 btc" | nobitex.py
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
