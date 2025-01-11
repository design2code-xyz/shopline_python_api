import time
import hmac
import json
from hashlib import sha256

try:
    import simplejson as json
except ImportError:
    import json
import re
from contextlib import contextmanager
from six.moves import urllib
from shopline.api_access import ApiAccess
from shopline.api_version import ApiVersion, Release, Unstable
import six
from shopline.utils import authorize


class ValidationException(Exception):
    pass


class Session(object):
    api_key = None
    secret = None
    protocol = "https"
    myshopline_domain = "myshopline.com"
    port = None

    @classmethod
    def setup(cls, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(cls, k, v)

    @classmethod
    @contextmanager
    def temp(cls, domain, version, token):
        import shopline

        original_domain = shopline.ShopLineResource.get_url()
        original_token = shopline.ShopLineResource.get_headers().get("Authorization")
        original_version = shopline.ShopLineResource.get_version() or version
        original_session = shopline.Session(original_domain, original_version, original_token)

        session = Session(domain, version, token)
        shopline.ShopLineResource.activate_session(session)
        yield
        shopline.ShopLineResource.activate_session(original_session)

    def __init__(self, handle, version=None, token=None, access_scopes=None, expiration_time=None):
        self.url = self.__prepare_url(handle)
        self.token = token
        self.version = ApiVersion.coerce_to_version(version)
        self.access_scopes = access_scopes
        self.expiration_time = expiration_time
        return

    def create_permission_url(self, scope, redirect_uri, responseType="code"):
        """get permission url by Herb"""
        print('redirect_uri', redirect_uri)
        query_params = dict(appKey=self.api_key, scope=",".join(scope), redirectUri=redirect_uri)
        if responseType:
            query_params["responseType"] = responseType
        return "https://%s/admin/oauth-web/#/oauth/authorize?%s" % (self.url, urllib.parse.urlencode(query_params))

    def get_by_net(self, url, data):
        timestamp = authorize.get_timestamp()
        # get post sign
        sign = authorize.get_sign(self.secret, timestamp, **data)
        headers = dict(appkey=self.api_key, sign=sign, timestamp=timestamp)
        headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, headers=headers, data=authorize.parse_json_data(**data), method="POST")
        response = urllib.request.urlopen(request)
        return response

    def request_token(self, params):
        code = params["code"]

        url = "https://%s/admin/oauth/token/create" % self.url

        data = dict(code=code)

        response = self.get_by_net(url, data)

        if response.code == 200:
            json_payload = json.loads(response.read().decode("utf-8"))
            if json_payload.get("code") == 200:
                data = json_payload.get("data", {})
                # print(json_payload)
                self.token = data["accessToken"]
                self.access_scopes = data["scope"]
                self.expiration_time = data["expireTime"]
                return self.token, self.access_scopes, self.expiration_time
            else:
                raise Exception("{}:{}".format(json_payload.get("i18nCode"), json_payload.get("message")))
        else:
            raise Exception(response.msg)

    def create_token(self, params):
        code = params["code"]

        url = "https://%s/admin/oauth/token/create" % self.url

        data = dict(code=code)

        response = self.get_by_net(url, data)

        if response.code == 200:
            json_payload = json.loads(response.read().decode("utf-8"))
            if json_payload.get("code") == 200:
                data = json_payload.get("data", {})
                # print(json_payload)
                self.token = data["accessToken"]
                self.access_scopes = data["scope"]
                self.expiration_time = data["expireTime"]
                return self.token, self.access_scopes, self.expiration_time
            else:
                raise Exception("{}:{}".format(json_payload.get("i18nCode"), json_payload.get("message")))
        else:
            raise Exception(response.msg)

    def refresh_token(self):
        """refresh token"""

        url = "https://%s/admin/oauth/token/refresh" % self.url
        data = dict()
        response = self.get_by_net(url, data)
        if response.code == 200:
            json_payload = json.loads(response.read().decode("utf-8"))
            if json_payload.get("code") == 200:
                data = json_payload.get("data", {})
                # print(json_payload)
                self.token = data["accessToken"]
                self.access_scopes = data["scope"]
                self.expiration_time = data["expireTime"]
                return self.token, self.access_scopes, self.expiration_time
            else:
                raise Exception("{}:{}".format(json_payload.get("i18nCode"), json_payload.get("message")))
        else:
            raise Exception(response.msg)

    def cancel(self):
        """
        cancel shop bind
        :return:
        """
        url = "https://%s/admin/oauth/authorize/cancel" % self.url
        data = dict()
        response = self.get_by_net(url, data)
        if response.code == 200:
            json_payload = json.loads(response.read().decode("utf-8"))
            if json_payload.get("code") == 200:
                data = json_payload.get("data", {})
                # print(json_payload)
                self.token = data["accessToken"]
                self.access_scopes = data["scope"]
                self.expiration_time = data["expireTime"]
                return self.token, self.access_scopes, self.expiration_time
            else:
                raise Exception("{}:{}".format(json_payload.get("i18nCode"), json_payload.get("message")))
        else:
            raise Exception(response.msg)

    @classmethod
    def validate_token(cls, params):
        ten_minutes = 36000
        if int(params.get("timestamp", 0)) < time.time() - ten_minutes:
            return False

        return True

    @property
    def api_version(self):
        return self.version

    @property
    def site(self):
        return self.version.api_path("%s://%s" % (self.protocol, self.url))

    @property
    def valid(self):
        return self.url is not None and self.token is not None

    @property
    def access_scopes(self):
        return self._access_scopes

    @access_scopes.setter
    def access_scopes(self, scopes):
        if scopes is None or type(scopes) == ApiAccess:
            self._access_scopes = scopes
        else:
            self._access_scopes = ApiAccess(scopes)

    @classmethod
    def __prepare_url(cls, url):
        if not url or (url.strip() == ""):
            return None
        url = re.sub("^https?://", "", url)
        shop = urllib.parse.urlparse("https://" + url).hostname
        if shop is None:
            return None
        idx = shop.find(".")
        if idx != -1:
            shop = shop[0:idx]
        if len(shop) == 0:
            return None
        shop += "." + cls.myshopline_domain
        if cls.port:
            shop += ":" + str(cls.port)
        return shop

    @classmethod
    def validate_params(cls, params):
        # Avoid replay attacks by making sure the request
        # isn't more than 10 minutes old.
        ten_minutes = 600
        if int(params.get("timestamp", 0)) < time.time() - ten_minutes:
            return False

        return cls.validate_sign(params)

    @classmethod
    def validate_sign(cls, params):
        if "sign" not in params:
            return False

        sign_calculated = cls.calculate_sign(params).encode("utf-8")
        sign_to_verify = params["sign"].encode("utf-8")

        # Try to use compare_digest() to reduce vulnerability to timing attacks.
        # If it's not available, just fall back to regular string comparison.
        try:
            return hmac.compare_digest(sign_calculated, sign_to_verify)
        except AttributeError:
            return sign_calculated == sign_to_verify

    @classmethod
    def calculate_sign(cls, params):
        """
        Calculate the HMAC of the given parameters in line with Shopify's rules for OAuth authentication.
        See http://docs.shopify.com/api/authentication/oauth#verification.
        """
        encoded_params = cls.__encoded_params_for_signature(params)
        # Generate the hex digest for the sorted parameters using the secret.
        return hmac.new(cls.secret.encode(), encoded_params.encode(), sha256).hexdigest()

    @classmethod
    def __encoded_params_for_signature(cls, params):
        """
        Sort and combine query parameters into a single string, excluding those that should be removed and joining with '&'
        """

        def encoded_pairs(params):
            for k, v in six.iteritems(params):
                if k == "sign":
                    continue

                if k.endswith("[]"):
                    # foo[]=1&foo[]=2 has to be transformed as foo=["1", "2"] note the whitespace after comma
                    k = k.rstrip("[]")
                    v = json.dumps(list(map(str, v)))

                # escape delimiters to avoid tampering
                k = str(k).replace("%", "%25").replace("=", "%3D")
                v = str(v).replace("%", "%25")
                yield "{0}={1}".format(k, v).replace("&", "%26")

        return "&".join(sorted(encoded_pairs(params)))
