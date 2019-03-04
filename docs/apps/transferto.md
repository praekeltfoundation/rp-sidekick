# RP TransferTo

While RapidPro does provide an integration with TransferTo to release airtime, it does not allow for the remuneration of data. This application more faithfully represents the REST API that TransferTo makes available and abstracts away the authentication.

A TransferTo account belongs to an Ogranization. You must pass in the organization id in the url path and the token used for authentication must belong to a user that belongs to the necessary organization. Set up the organization and transferto account in the django admin.

### Synchronous Endpoints
- `Ping`: check that our authentication to TransferTo is working
- `MsisdnInfo`: get information about an MSISDN
- `ReserveId`: get ID for a purchase transaction in the future
- `GetCountries`: get the countries that a particular account can
- `GetOperators`: get mobile network operators (MNO) for a country
- `GetOperatorAirtimeProducts`: get products list and prices (wholesale and retail) specific to your account
- `GetOperatorProducts`: get products offered by a particular MNO
- `GetCountryServices`: get services available in a particular country
- `TopUpData`: an endpoint that immediately returns a 200 status code and then starts a Celery task to get information about a number, send the reward and update the necessary fields in RapidPro.

### Asyncronous Endpoints
These endpoints will queue the request to TransferTo using celery. They will immediately respond with a 200 response code once the task is queued, preventing any timeouts on RapidPro. Use the `flow_uuid_key` arg to get the tasks to start the participant on a new flow, assuming that it works according to plan.

- `BuyProductTakeAction`: this endpoint allows the user to
    - purchase a product for a particular msisdn
    - [optional] update a rapidpro contact's fields based on the response
    - [optional] start the participant on another rapidpro flow, once the task has been completed.

- `BuyAirtimeTakeAction`: this endpoint allows the user to
    - purchase airtime for a particular msisdn
    - [optional] update a rapidpro contact's fields based on the response
    - [optional] start the participant on another rapidpro flow, once the task has been completed.

    ! Note that the 'from' argument should not be longer than 15 characters as TransferTo will truncate the characters in the SMS that it sends.
