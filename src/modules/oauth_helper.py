import urllib.parse
import hmac
import hashlib
import base64
import time
import random
import string

class OAuthHelper:
    @staticmethod
    def generate_oauth_signature(method, url, params, consumer_secret, token_secret='', signature_method='HMAC-SHA1'):
        base_string = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote('&'.join(['{}={}'.format(urllib.parse.quote(k, safe=''), urllib.parse.quote(str(v), safe='')) for k, v in sorted(params.items())]), safe='')
        ])
        key = '{}&{}'.format(consumer_secret, token_secret)
        if signature_method == 'HMAC-SHA256':
            hashed = hmac.new(key.encode(), base_string.encode(), hashlib.sha256)
        else:
            hashed = hmac.new(key.encode(), base_string.encode(), hashlib.sha1)
        return base64.b64encode(hashed.digest()).decode()

    @staticmethod
    def generate_oauth_params(method, url, consumer_key, consumer_secret, token='', token_secret='', signature_method='HMAC-SHA1'):
        oauth_params = {
            'oauth_consumer_key': consumer_key,
            'oauth_nonce': ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8)),
            'oauth_signature_method': signature_method,
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0'
        }
        if token:
            oauth_params['oauth_token'] = token

        parsed_url = urllib.parse.urlparse(url)
        query_params = dict(urllib.parse.parse_qsl(parsed_url.query))
        all_params = {**query_params, **oauth_params}

        oauth_signature = OAuthHelper.generate_oauth_signature(method, parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path, all_params, consumer_secret, token_secret, signature_method)
        oauth_params['oauth_signature'] = oauth_signature

        return oauth_params

    @staticmethod
    def generate_oauth_url(method, url, consumer_key, consumer_secret, token='', token_secret='', signature_method='HMAC-SHA1'):
        parsed_url = urllib.parse.urlparse(url)
        existing_params = dict(urllib.parse.parse_qsl(parsed_url.query))

        oauth_params = OAuthHelper.generate_oauth_params(method, url, consumer_key, consumer_secret, token, token_secret, signature_method)

        all_params = {**existing_params, **oauth_params}

        all_query_string = '&'.join(['{}={}'.format(urllib.parse.quote(k, safe=''), urllib.parse.quote(str(v), safe='')) for k, v in all_params.items()])

        final_url = '{}://{}{}?{}'.format(parsed_url.scheme, parsed_url.netloc, parsed_url.path, all_query_string)

        return final_url
