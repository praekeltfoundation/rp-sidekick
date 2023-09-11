from sidekick.tests.utils import create_org

from ..models import DtoneAccount


def create_dtone_account(org=None, **kwargs):
    if not org:
        org = create_org()
    data = {
        "name": "fake account",
        "apikey": "fake_apikey",
        "apisecret": "fake_apisecret",
        "production": False,
    }
    data.update(kwargs)
    return DtoneAccount.objects.create(org=org, **data)
