from randomisation.models import Arm, Strata, StrataOption, Strategy

DEFAULT_STRATEGY = {
    "name": "Test Strategy",
    "arms": [
        {"name": "Arm 1", "weight": 1},
        {"name": "Arm 2", "weight": 1},
        {"name": "Arm 3", "weight": 1},
    ],
    "stratas": [
        {"name": "Age Group", "options": ["18-29", "29-39"]},
        {"name": "Province", "options": ["WC", "GT"]},
    ],
}


def create_test_strategy(data=DEFAULT_STRATEGY):
    strategy = Strategy.objects.create(name=data["name"])

    for arm in data["arms"]:
        Arm.objects.create(strategy=strategy, name=arm["name"], weight=arm["weight"])

    for strata_data in data["stratas"]:
        strata = Strata.objects.create(name=strata_data["name"])

        for option in strata_data["options"]:
            StrataOption.objects.create(strata=strata, description=option)

        strategy.stratas.add(strata)

    return strategy
