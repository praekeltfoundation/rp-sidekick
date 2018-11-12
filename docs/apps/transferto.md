# RP TransferTo

While RapidPro does provide an integration with TransferTo to release airtime, it does not allow for the remuneration of data. This application more faithfully represents the REST API that TransferTo makes available and abstracts away the authentication.

- `Ping`: check that our authentication to TransferTo is working
- `MsisdnInfo`: get information about an MSISDN
- `ReserveId`: get ID for a purchase transaction in the future
- `GetCountries`: get the countries that a particular account can
- `GetOperators`: get mobile network operators (MNO) for a country
- `GetOperatorAirtimeProducts`: get products list and prices (wholesale and retail) specific to your account
- `GetOperatorProducts`: get products offered by a particular MNO
- `GetCountryServices`: get services available in a particular country
- `TopUpData`: an endpoint that immediately returns a 200 status code and then starts a Celery task to get information about a number, send the reward and update the necessary fields in RapidPro.

## Sidekick Endpoints
- `BuyProductTakeAction`: this endpoint allows the user to
    - purchase a product for a particular msisdn
    - [optional] update a rapidpro contact's fields based on the response
    - [optional] start the participant on another rapidpro flow, once the task has been completed.
