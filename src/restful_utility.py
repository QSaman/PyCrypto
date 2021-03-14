import hmac
import hashlib

ENCODING = "utf-8"

def create_hmac_sha256_signature(message, secret_key):
    secret_key_in_bytes = secret_key.encode(ENCODING)
    message_in_bytes = message.encode(ENCODING)
    signature = hmac.new(secret_key_in_bytes, message_in_bytes, hashlib.sha256).hexdigest()
    return signature

def convert_dictionary_to_query_string(my_dict):
    first = True
    message = ""
    for key, value in my_dict.items():
        if first:
            message += "{0}={1}".format(key, value)
            first = False
        else:
            message += "&{0}={1}".format(key, value)
    return message
