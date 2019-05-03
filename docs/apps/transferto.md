# RP TransferTo (DTOne integration)

_Please note that since building this package, the company formerly known as TransferTo, rebranded to DTOne. The docs will refer to DTOne where possible, but most of the code still refers to TransferTo._

While RapidPro does provide an integration with DTOne (previously TransferTo) to release airtime, it does not allow for the remuneration of data. This application more faithfully represents the REST API that DTOne makes available and abstracts away the authentication.

A TransferTo account belongs to an Ogranization. You must pass in the organization id in the url path and the token used for authentication must belong to a user that belongs to the necessary organization. Set up the organization and transferto account in the django admin.

### Synchronous Endpoints
- `Ping`: check that our authentication to DTOne is working
- `MsisdnInfo`: get information about an MSISDN
- `ReserveId`: get ID for a purchase transaction in the future
- `GetCountries`: get the countries that a particular account can
- `GetOperators`: get mobile network operators (MNO) for a country
- `GetOperatorAirtimeProducts`: get products list and prices (wholesale and retail) specific to your account
- `GetOperatorProducts`: get products offered by a particular MNO
- `GetCountryServices`: get services available in a particular country
- `TopUpData`: an endpoint that immediately returns a 200 status code and then starts a Celery task to get information about a number, send the reward and update the necessary fields in RapidPro.

### Asyncronous Endpoints
These endpoints will queue the request to DTOne using celery. They will immediately respond with a 200 response code once the task is queued, preventing any timeouts on RapidPro. Use the `flow_uuid_key` arg to get the tasks to start the participant on a new flow, assuming that it works according to plan.

- `BuyProductTakeAction`: this endpoint allows the user to
    - purchase a product for a particular msisdn
    - (optional) update a rapidpro contact's fields based on the response
    - (optional) start the participant on another rapidpro flow, once the task has been completed.
- `BuyAirtimeTakeAction`: this endpoint allows the user to
    - purchase airtime for a particular msisdn
    - (optional) update a rapidpro contact's fields based on the response. Use the query parameters `user_uuid_key` as well as the
    - (optional) start the participant on another rapidpro flow, if the request to DTOne was successful
    - (optional) start the participant on another rapidpro flow, if the request to DTOne failed or was rejected

    ! Note that the `from` argument should not be longer than 15 characters as DTOne will truncate the characters in the SMS that it sends.

#### 'Take Action' query parameter set up

The query paramater keys are as follows

- `user_uuid_key`- This is the most important argument and required for any of the actions to take place. If it is not provided, Sidekick cannot complete any actions. This should can set within the RapidPro flow using the `@contact.uuid` field, so that the param looks like this: `user_uuid=@contact.uuid`
- `flow_uuid_key` - This is the uuid of the flow that should be taken, if the DTOne purchase is successful. Provide the UUID of the flow as an argument. e.g. `flow_uuid_key=c1ac0ed4-61db-4886-afe1-yfb484cdcef1`
- `fail_flow_uuid_key` - This is the uuid of the flow that should be taken, if the DTOne purchase is *not* successful. Provide the UUID of the flow as an argument. e.g. `fail_flow_uuid_key=c1ac01d4-61d6-4d86-afe1-yfb484cdcef1`
- Finally, the rest of the query params given, are interpreted as arguments that should be updated. This maps from `key=value` to `rapidpro field = DTOne field`.
E.g. say we have a RapidPro field called `dtone_error_text` and we want to update it with the error message that we get back from DTOne, which is labelled as `error_txt` in the response from DTOne. So we would provide the following argument: `dtone_error_text=error_txt`. So once the operation is completed, and assuming the transfer is successful, the specific contact's RapidPro field called `dtone_error_text` will have the value of `Transaction successful`.
Note that we can provide multiple arguments for the updating of values

As a final example, the complete query parameter, assuming you've used all of the arguments, might look something like this:

`user_uuid=@contact.uuid`

`flow_uuid_key=c1ac0ed4-61db-4886-afe1-yfb484cdcef1`

`fail_flow_uuid_key=c1ac01d4-61d6-4d86-afe1-yfb484cdcef1`

`tp_requested=product_requested`

`tp_error_code=error_code`

`tp_error_txt=error_txt`

Which when parameterized, would look like this:

`?user_uuid=@contact.uuid&flow_uuid_key=c1ac0ed4-61db-4886-afe1-yfb484cdcef1&fail_flow_uuid_key=c1ac01d4-61d6-4d86-afe1-yfb484cdcef1&tp_requested=product_requested&tp_error_code=error_code&tp_error_txt=error_txt`

#### Email Error Reporting
Using the 'point of contact' email field listed under an organisation, you can update this to receive emails that will notify an account, should something go wrong during the remuneration, starting of flows and/or updating of fields. This is useful for testing and making sure that things work as expected as well. E.g. noting whether the flow uuid's are correct and that the specified fields exist.

Note that this currently only works for the airtime endpoint, not the purchase of products.
