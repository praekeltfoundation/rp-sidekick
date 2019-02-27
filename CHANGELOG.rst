VERSIONS
========

Next Release
------------

1.3.0
------------
* TransferTo: allow multiple transferto accounts

1.2.1
------------
* Reformat with updated black package

1.2.0
------------
* Sidekick: Added a check contact endpoint for WhatsApp

1.1.0
------------
* Sidekick: Fixed document structure and updated docs
* Sidekick: updated WA templated message endpoint to accept multiple localizable params
* BREAKING: any flows that call the /send_template/ endpoints must change the param `message=` to `0=`

1.0.17
------------
* TransferTo: Added error code to responses where TransferToClient returns an error


1.0.16
------------
* ASOS: Fixed notification for empty screening record.

1.0.15
------------
* TransferTo: added hacky fallback method for product purchase and take action task

1.0.14
------------
* TransferTo: refactored task functionality into to take_action function - updates RapidPro fields and/or starts another flow
* TransferTo: add endpoint which purchases airtime, then updates RapidPro state with new take_action function
* Sidekick: add email functionality in settings
* TransferTo: send email on TransferTo failure task; buy_product_take_action

1.0.13
------------
* TransferTo: default to using cached msisdn number in views
* TransferTo: add endpoint which purchases product then updates fields and/or starts another flow

1.0.12
------------
 * TransferTo: store data on number in database
 * TransferTo: use cached msisdn number in tasks
 * TransferTo: refactored tests for tasks
 * Redcap: Allow blank Nomination url
 * Redcap: Send names when starting patient reminder flow

1.0.11
------------
 * Install PyCap from Github commit until they make a release(temporary)
 * Add Hospital and PatientRecord to admin site

1.0.10
------------
 * Added function to do WhatsApp contact check
 * Added function to update Rapidpro Contact with WhatsApp ID
 * Redcap: Added tasks to send patient data collection reminders
 * Redcap: Fixed updated_at field for values

1.0.9
------------
 * Django version bump

1.0.8
------------
 * Clean message before sending to Engage

1.0.7
------------
 * Endpoint to send templated WhatsApp messages to Engage.
