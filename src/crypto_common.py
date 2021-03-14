import json
import time
import requests

from pathlib import Path, PurePath

class RatesCache:
    def __init__(self, rates_endpoint, cache_expiry_in_seconds, load_json_response_callback, cache_directory, rates_filename):
        self.rates_endpoint = rates_endpoint
        self.cache_expiry_in_seconds = cache_expiry_in_seconds
        self.load_json_response_callback = load_json_response_callback
        self.cache_directory = cache_directory
        self.rates_filename = rates_filename
        self.timestamp = None
        
    def download_rates(self):
        self.timestamp = time.time()
        response_http = requests.get(self.rates_endpoint)
        if not response_http.ok:
            quit(response_http.text)
        response = response_http.json()
        response.update({'timestamp' : self.timestamp})
        
        cache_dir_path = Path(self.cache_directory)
        if not cache_dir_path.exists():
            cache_dir_path.mkdir(parents=True)
            
        with open(self.rates_filename, "w") as f:
            f.write(json.dumps(response, indent=2))
            
        self.load_json_response_callback(response)
        
    def is_cache_expired(self):
        cur_timestamp = time.time()
        return (cur_timestamp - self.timestamp) > self.cache_expiry_in_seconds
        
    def get_prices(self):
        if self.timestamp is None:
            cache_dir_path = Path(self.cache_directory)
            if cache_dir_path.exists():
                try:
                    with open(self.rates_filename, "r") as f:
                        json_response = json.loads(f.read())
                        self.timestamp = json_response['timestamp']
                        if self.is_cache_expired():
                            self.download_rates()
                        else:
                            self.load_json_response_callback(json_response)
                except IOError: 
                    self.download_rates()
            else:
                cache_dir_path.mkdir(parents=True)
                self.download_rates()
                
        elif self.is_cache_expired():
            self.download_rates()
