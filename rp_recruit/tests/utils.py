import uuid

from sidekick.tests.utils import create_org

from ..models import Recruitment


def create_recruitment(org=None, **kwargs):
    if not org:
        org = create_org()
    data = {
        "name": "Test Recruitment",
        "term_and_conditions": "terms and conditions",
        "rapidpro_flow_uuid": str(uuid.uuid4()),
        "rapidpro_pin_key_name": "fake_rapidpro_pin_key_name",
        "rapidpro_group_name": "fake_rapidpro_group_name",
    }
    data.update(kwargs)
    return Recruitment.objects.create(org=org, **data)
