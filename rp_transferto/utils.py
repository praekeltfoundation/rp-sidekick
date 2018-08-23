import requests
import time
import hashlib


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

    def _make_transferto_request(self, action, url=None, **kwargs):
        """
        Returns a dict with response from the TransferTo API

        Reduces the boilerplate for constructing TransferTo requests
        """
        key = str(int(1000000 * time.time()))
        md5 = hashlib.md5(
            (self.login + self.token + key).encode("UTF-8")
        ).hexdigest()
        data = dict(login=self.login, key=key, md5=md5, action=action, **kwargs)
        if url is None:
            url = self.url
        response = requests.post(url, data=data)
        return self._convert_response_body(response.content)

    def ping(self):
        """
        Check API status
        """
        return self._make_transferto_request("ping")

    def get_misisdn_info(self, msisdn):
        """
        Returns dict with information for a given MSISDN
        """
        action = "msisdn_info"
        return self._make_transferto_request(action, destination_msisdn=msisdn)

    def reserve_id(self):
        """
        Returns dict with information for a given MSISDN
        """
        action = "reserve_id"
        return self._make_transferto_request(action)

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

    def get_operator_products(self, operator_id):
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
