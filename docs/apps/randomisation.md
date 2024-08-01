# Randomisation

This app is used to configure randomisation strategies that can be used in studies. Currently we only have stratification implemented but we can add other strategy types at a later stage.

### Models

- `Strata`: To configure strata and their valid options.
- `Strategy`: To configure the randomisation strategy which consists of stratas and arms.
- `Arm`: Study arm that gets linked to a strategy, has a weight field that defaults to one, we use this in the randomisation to determine how often this arm will be selected.
- `StrataOption`: Options linked to strata. We use this to validate data we receive.
- `StrataMatrix`: To keep record of strata and which arms we need to return.

### API

These endpoint are both POST requests and have the same input format.

Example request body if we configured stratas for gender and province:
```
{
	"gender": "male",
	"province": "WC"
}
```

- `<int:strategy_id>/validate_strata_data/`: To check if strata data is valid without returning a arm. We use this to know we can request consent from the user, if they consent we use the `get_random_arm` endpoint to get a arm.
	- Valid response: `200 {"valid": true}`
	- Invalid response: `200 {"valid": false, "error": "<reason for not being valid>"}`
- `<int:strategy_id>/get_random_arm/`: To get a random arm for the strata data provided.
	- Successful response: `200 {"arm": "test arm"}`
	- Error response: `400 {"error":"<validation errors>"}`
