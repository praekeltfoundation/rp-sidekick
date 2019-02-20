# RP Sidekick
The default Sidekick Module exists to provide shareable components across the various django applications, in particular the Org and User management. It also provides some miscellaneous functionality, in particular, the ability to send WhatsApp templated messages

## Check WhatsApp Endpoint
This endpoint, served at `/check_contact/<org_id>/<msisdn>/` serves as a wrapper for a single request to the [Turn contact check endpoint](https://whatsapp.praekelt.org/docs/index.html#contacts).

## WhatsApp Template Endpoint
RapidPro does not yet provide first-class support for [WhatsApp templates](https://whatsapp.praekelt.org/docs/index.html#templated-messages), which means that they need to be sent via Sidekick, using a Webhook within RapidPro.

### Required Parameters
- `org_id`: this refers to the Organisation created within Sidekick. You can find this in the Admin page. There is a 1-to-1 mapping between the Org and a Turn account. Make sure you have added the necessary credentials to your Org.
- `wa_id`: this will be the number of the individual you wish to contact. In RapidPro flows, this can be accessed using `@contact.whatsapp`
- `element_name`: the name of the template that you are using. You will have created this when submitting it to WhatsApp for approval.
- `namespace`: this argument will likely be fixed across your organisation. Check previous uses or check with whoever set up your WA account.

### Localized Parameters
Templated messages allow you to pass in variables. See the [Turn documentation](https://whatsapp.praekelt.org/docs/index.html#localizable-parameters-for-templated-messages) for more details. These can be passed to the endpoint by numbering your param arguments. e.g. `0=R25&1=24` will pass the parameters `R25` and `24` to the template, in that order.
Note that this endpoint only orders the arguments, it does not attempt to skip over arguments. Thus `0=R25&1=24`, `1=R25&2=24` and `1=R25&99=24` will all be treated in an identical manner.
