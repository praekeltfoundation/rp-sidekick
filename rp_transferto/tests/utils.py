from sidekick.tests.utils import create_org

from ..models import TransferToAccount


def create_transferto_account(org=None, **kwargs):
    if not org:
        org = create_org()
    data = {
        "login": "fake_login",
        "token": "fake_token",
        "apikey": "fake_apikey",
        "apisecret": "fake_apisecret",
    }
    data.update(kwargs)
    return TransferToAccount.objects.create(org=org, **data)
