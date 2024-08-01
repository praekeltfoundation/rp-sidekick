import random

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from randomisation.models import StrataMatrix


def validate_stratification_data(strategy, data):
    """
    Validates that the data dict received is valid compared to the strategy
    configuration.
    """
    try:
        schema = {
            "type": "object",
            "properties": {},
            "required": [strata.slug for strata in strategy.stratas.all()],
            "additionalProperties": False,
        }

        for strata in strategy.stratas.all():
            options = [option.description for option in strata.options.all()]
            schema["properties"][strata.slug] = {"type": "string", "enum": options}

        validate(instance=data, schema=schema)
    except ValidationError as e:
        return e.message


def get_random_stratification_arm(strategy, data):
    """
    Get or create a strata matrix object for the given data and returns the next arm,
    it will delete the matrix record if the last arm in the matrix was returned.
    """
    matrix, created = StrataMatrix.objects.get_or_create(
        strategy=strategy, strata_data=data
    )

    if created:
        study_arms = []
        for arm in strategy.arms.all():
            study_arms += [arm.name] * arm.weight

        random.shuffle(study_arms)
        random_arms = study_arms
        matrix.arm_order = ",".join(study_arms)
    else:
        random_arms = matrix.arm_order.split(",")

    arm = random_arms[matrix.next_index]

    if matrix.next_index + 1 == len(random_arms):
        matrix.delete()
    else:
        matrix.next_index += 1
        matrix.save()

    return arm
