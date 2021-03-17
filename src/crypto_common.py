import json
import time
import requests
import decimal
import tempfile

from pathlib import Path, PurePath
from abc import ABCMeta, abstractmethod

cache_directory_base = PurePath(tempfile.gettempdir(), 'py_crypto')

class CacheManager(metaclass=ABCMeta):
    def __init__(self, cache_endpoint, cache_expiry_in_seconds, cache_directory, cache_filename):
        self.cache_endpoint = cache_endpoint
        self.cache_expiry_in_seconds = cache_expiry_in_seconds
        self.cache_directory = cache_directory
        self.cache_filename = cache_filename
        self.timestamp = None
        
    # This method is responsible to downloading from endpoint
    @abstractmethod
    def download_cache(self):
        pass
    
    # When the responsed is received, this method is responsible to extract data from it
    @abstractmethod
    def refresh_cache(self, response):
        pass
    
    def refresh_cache_file(self):
        self.timestamp = time.time()
        
        response = self.download_cache()
        
        if isinstance(response, dict):
            response.update({'timestamp' : self.timestamp})
        elif isinstance(response, list):
            response.append({'timestamp' : self.timestamp})
        else:
            raise Exception('returned Json response is unsupported: {0}'.format(response_http.text))
        
        cache_dir_path = Path(self.cache_directory)
        if not cache_dir_path.exists():
            cache_dir_path.mkdir(parents=True)
            
        with open(self.cache_filename, "w") as f:
            f.write(json.dumps(response, indent=2))
        
        self.refresh_cache(response)
        
    def is_cache_expired(self):
        cur_timestamp = time.time()
        return (cur_timestamp - self.timestamp) > self.cache_expiry_in_seconds
    
    def load_cache(self):
        if self.timestamp is None:
            cache_dir_path = Path(self.cache_directory)
            if cache_dir_path.exists():
                try:
                    with open(self.cache_filename, "r") as f:
                        json_response = json.loads(f.read())
                        if isinstance(json_response, dict):
                            self.timestamp = json_response['timestamp']
                        elif isinstance(json_response, list):
                            for item in json_response:
                                if 'timestamp' in item:
                                    self.timestamp = item['timestamp']
                                    break
                        if self.is_cache_expired():
                            self.refresh_cache_file()
                        else:
                            self.refresh_cache(json_response)
                except IOError: 
                    self.refresh_cache_file()
            else:
                cache_dir_path.mkdir(parents=True)
                self.refresh_cache_file()
                
        elif self.is_cache_expired():
            self.refresh_cache_file()

class RatesCache(CacheManager):
    def __init__(self, rates_endpoint, cache_expiry_in_seconds, load_json_response_callback, cache_directory, rates_filename):
        super().__init__(rates_endpoint, cache_expiry_in_seconds, cache_directory, rates_filename)
        self.load_json_response_callback = load_json_response_callback
        
    def get_prices(self):
        super().load_cache()
        
    def download_cache(self):
        response_http = requests.get(self.cache_endpoint)
        if not response_http.ok:
            quit(response_http.text)
        response = response_http.json(parse_float=str)
        return response
    
    def refresh_cache(self, response):
        self.load_json_response_callback(response)
