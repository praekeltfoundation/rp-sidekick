# RP Sidekick
The default Sidekick Module exists to provide shareable components across the various django applications, in particular the Org and User management. It also provides some miscellaneous functionality, in particular, the ability to send WhatsApp templated messages

## Orgs
Sidekick provides an Organization model, to manage and match an Org within RapidPro. This is used as a building block for the rest of the functionality that the framework provides, for example it can be linked to

- `name` - name given to the Org on Sidekick. We recommend giving it the same name as the RapidPro Org.
- `url` - the url of the RapidPro instance that the Org belongs to.
- `token` - the auth token for a RapidPro user, to get API access to the RP Org. Note that this needs active amangement as the user in question could destroy and recreate their token on RapidPro, rendering much of the functionality of Sidekick useless until this is updated.
- `users` - this links the Django user model. Sidekick does not currently use the Django permissions framework and so belonging to an Org provides default access to all applications.
- `engage_url` - the URL of the service used for WhatsApp messaging.
- `engage_token` - the auth token for the WhatsApp service.
- `point_of_contact` - an email address to surface any immediate issues.

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

You will also need to make sure that the values you pass as parameters should be encoded. For example, `&` should be represented by `%26`. You can do this using python's `urllib` library:

```{python}
>>> from urllib.parse import urlencode
>>> params = {'lang':'en','tag':'python is great 10% of the time'}
>>> urlencode(params)
'lang=en&tag=python+is+great+10%25+of+the+time'
```
