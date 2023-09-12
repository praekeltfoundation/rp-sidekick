from urllib.parse import urljoin

import requests


class DtoneClient:
    def __init__(self, apikey, apisecret, production):
        self.auth = requests.auth.HTTPBasicAuth(apikey, apisecret)

        if production:
            self.base_url = "https://dvs-api.dtone.com"
        else:
            self.base_url = "https://preprod-dvs-api.dtone.com"

    def get_operator_id(self, msisdn):
        response = requests.get(
            urljoin(self.base_url, f"/v1/lookup/mobile-number/{msisdn}"),
            auth=self.auth,
        )
        response.raise_for_status()
        if len(response.json()) > 0:
            return response.json()[0]["id"]

    def get_fixed_value_product(self, operator_id, value):
        response = requests.get(
            urljoin(
                self.base_url,
                f"/v1/products?type=FIXED_VALUE_RECHARGE&operator_id={operator_id}&per_page=100",
            ),
            auth=self.auth,
        )
        response.raise_for_status()

        for product in response.json():
            if product["destination"]["amount"] == value:
                return product["id"]

    def submit_transaction(self, transaction_uuid, msisdn, product_id):
        body = {
            "external_id": transaction_uuid,
            "product_id": product_id,
            "auto_confirm": True,
            "credit_party_identifier": {"mobile_number": msisdn},
        }

        return requests.post(
            urljoin(
                self.base_url,
                "/v1/async/transactions",
            ),
            auth=self.auth,
            json=body,
        )
