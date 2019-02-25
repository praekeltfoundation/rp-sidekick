from ..models import Organization


def create_org(**kwargs):
    data = {
        "name": "Test Organization",
        "url": "http://localhost:8002/",
        "token": "REPLACEME",
        "engage_url": "http://whatsapp/",
        "engage_token": "test-token",
    }
    data.update(kwargs)
    return Organization.objects.create(**data)
