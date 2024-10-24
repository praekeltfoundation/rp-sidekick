from ..models import Organization


def create_org(**kwargs):
    data = {
        "name": "Test Organization",
        "url": "http://localhost:8002/",
        "token": "REPLACEME",
        "engage_url": "http://whatsapp/",
        "engage_token": "test-token",
        "contentrepo_url": "http://contentrepo",
        "contentrepo_token": "test-token",
    }
    data.update(kwargs)
    return Organization.objects.create(**data)


def assertCallMadeWith(call, **kwargs):
    """
    Check a sub-list of function calls, rather than the entire function call

    This is particularly useful when a Call contains a reference to self,
    which is difficult to reference in a test
    """
    call_args, call_kwargs = call

    if call_kwargs:
        missing_keys = []
        matching_keys_incorrect_value = []
        for key in kwargs:
            # get a list of all of the keywords that are _not_ in kwargs
            if key not in call_kwargs:
                missing_keys.append(key)
            # get a list of all of the keywords that do not have matching objects
            elif call_kwargs[key] != kwargs[key]:
                matching_keys_incorrect_value.append(
                    (key, call_kwargs[key], kwargs[key])
                )

        error_messages = []
        if any(missing_keys):
            error_messages.append("missing keyword args from call:")
            [error_messages.append(f"\t{missing_key}") for missing_key in missing_keys]
        if any(matching_keys_incorrect_value):
            error_messages.append("incorrect args for given keyword:")
            [
                error_messages.append(
                    f"{_key}:\n\texpected: {expected_value}\n\tactual: {actual_value}"
                )
                for _key, actual_value, expected_value in matching_keys_incorrect_value
            ]
        if error_messages:
            raise AssertionError("\n".join(error_messages))
