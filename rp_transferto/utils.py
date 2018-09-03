import requests
import time
import hashlib
import hmac
import base64


class TransferToClient:
    def __init__(self, login, token):
        self.login = login
        self.token = token
        self.url = "https://airtime.transferto.com/cgi-bin/shop/topup"

    def _convert_response_body(self, body_text):
        """
        Returns a dict of the airtime API body response
        """
        lines = body_text.decode("utf8").strip().split("\r\n")
        data = {}
        for line in lines:
            [key, value] = line.split("=")
            data[key] = value
        return data

    def _make_transferto_request(self, action, **kwargs):
        """
        Returns a dict with response from the TransferTo API

        Reduces the boilerplate for constructing TransferTo requests
        """
        key = str(int(1000000 * time.time()))
        md5 = hashlib.md5(
            (self.login + self.token + key).encode("UTF-8")
        ).hexdigest()
        data = dict(login=self.login, key=key, md5=md5, action=action, **kwargs)
        response = requests.post(self.url, data=data)
        return self._convert_response_body(response.content)

    def ping(self):
        """
        Check API status
        """
        return self._make_transferto_request(action="ping")

    def get_misisdn_info(self, msisdn):
        """
        Returns dict with information for a given MSISDN
        """
        return self._make_transferto_request(
            action="msisdn_info", destination_msisdn=msisdn
        )

    def reserve_id(self):
        """
        Returns dict with id for future transaction
        """
        return self._make_transferto_request(action="reserve_id")

    def get_countries(self):
        """
        Returns list of countries offered to your TransferTo account
        """
        return self._make_transferto_request(
            action="pricelist", info_type="countries"
        )

    def get_operators(self, country_id):
        """
        Return the list of operators offered to your account, for a specific country

        @param:integer country_id
        """
        if type(country_id) != int:
            raise TypeError("arg must be an int")
        else:
            return self._make_transferto_request(
                action="pricelist", info_type="country", content=country_id
            )

    def get_operator_airtime_products(self, operator_id):
        """
        Returns the list of denomination including wholesale and retail prices offered to your account,
        for a specific operator
        """
        if type(operator_id) != int:
            raise TypeError("arg must be an int")
        else:
            return self._make_transferto_request(
                action="pricelist", info_type="operator", content=operator_id
            )

    def make_topup(
        self,
        msisdn,
        product,
        source_msisdn=None,
        source_name=None,
        reserve_id=None,
    ):
        """
        Returns the list of denomination including wholesale and retail prices offered to your account,
        for a specific operator
        """
        if source_msisdn is None and source_name is None:
            raise Exception("source_msisdn and source_name cannot both be None")
        if type(product) != int:
            raise TypeError("product arg must be an int")

        keyword_args = {
            "action": "topup",
            "destination_msisdn": msisdn,
            "msisdn": source_msisdn or source_name,
            "product": product,
        }

        if reserve_id:
            keyword_args["reserve_id"] = reserve_id

        return self._make_transferto_request(**keyword_args)


class TransferToClient2:
    def __init__(self, apikey, apisecret):
        self.apikey = apikey
        self.apisecret = apisecret

    def _make_transferto_api_request(self, url):
        nonce = int(time.time())
        message = bytes((self.apikey + str(nonce)).encode("utf-8"))
        secret = bytes(self.apisecret.encode("utf-8"))
        transferto_hmac = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        )

        headers = {}
        headers["X-TransferTo-apikey"] = self.apikey
        headers["X-TransferTo-nonce"] = str(nonce)
        headers["x-transferto-hmac"] = transferto_hmac

        response = requests.get(url, headers=headers)
        return response.json()

    def get_operator_products(self, operator_id):
        product_url = "https://api.transferto.com/v1.1/operators/{}/products".format(
            operator_id
        )
        return self._make_transferto_api_request(product_url)

    def get_country_services(self, country_id):

        service_url = "https://api.transferto.com/v1.1/countries/{}/services".format(
            country_id
        )
        return self._make_transferto_api_request(service_url)

    def topup_data(self, msisdn, product_id, simulate=False):
        external_id = str(int(1000 * time.time()))
        # now create the json object that will be used
        simulation = "1" if simulate else "0"
        mobile_number = msisdn.replace("+", "")
        fixed_recharge = {
            "account_number": mobile_number,
            "product_id": product_id,
            "external_id": external_id,
            "simulation": simulation,
            "sender_sms_notification": "1",
            "sender_sms_text": "Sender message",
            "recipient_sms_notification": "1",
            "recipient_sms_text": "MomConnect",
            "sender": {
                "last_name": "",
                "middle_name": " ",
                "first_name": "",
                "email": "",
                "mobile": "08443011",
            },
            "recipient": {
                "last_name": "",
                "middle_name": "",
                "first_name": "",
                "email": "",
                "mobile": mobile_number,
            },
        }

        nonce = int(time.time())
        message = bytes((self.apikey + str(nonce)).encode("utf-8"))
        secret = bytes(self.apisecret.encode("utf-8"))
        transferto_hmac = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        )
        headers = {}
        headers["X-TransferTo-apikey"] = self.apikey
        headers["X-TransferTo-nonce"] = str(nonce)
        headers["x-transferto-hmac"] = transferto_hmac
        response = requests.post(
            "https://api.transferto.com/v1.1/transactions/fixed_value_recharges",
            headers=headers,
            json=fixed_recharge,
        )
        return response.json()
