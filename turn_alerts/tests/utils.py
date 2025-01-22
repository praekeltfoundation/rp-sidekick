from sidekick.tests.utils import create_org
from turn_alerts.models import TurnActions


def create_turn_action(org=None, **kwargs):
    if not org:
        org = create_org()
    data = {
        "journey_id": "fake_journey_id",
        "error_code": 131026,
    }
    data.update(kwargs)
    return TurnActions.objects.create(org=org, **data)
