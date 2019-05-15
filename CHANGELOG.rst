VERSIONS
========

Next Release
------------

1.5.6
------------
ASOS: Steering committee notification on outdated screening records.

1.5.5
------------
ASOS: Fix the group invite message.

1.5.4
------------
ASOS: Search for contacts by Tel and WhatsApp ID before trying to create.

1.5.3
------------
ASOS: Allow nulls on patient record date

1.5.2
------------
ASOS: Fix starting of the patient data check task again
ASOS: Use new template

1.5.1
------------
ASOS: New patient reminder template and update screening record fields

1.5.0
------------
Sidekick: added prometheus metrics endpoint and view metrics
TransferTo: added prometheus metrics for DTOne/TransferTo call

1.4.8
------------
ASOS: Fix starting of the patient data check task

1.4.7
------------
ASOS: Add total eligble field to the screening record model

1.4.6
------------
ASOS: Save screening record when running the Patient Data Check task.
ASOS: Link patient records to hospitals

1.4.5
------------
ASOS: Create WA group per hospital, notification will be sent there if hospital lead is a member.

1.4.4
------------
TransferTo: fix email bug where it always reported topup request as a success
Sidekick: create Token automatically when a user is created, using Django signals

1.4.3
------------
Sidekick: new detailed health endpoint that will check db connection and celery queue status

1.4.2
------------
* TransferTo: fixed logic bugs in BuyAirtimeTakeAction task, causing nonsensical email reporting output and updated email formatting

1.4.1
------------
* Sidekick: fixed bug where authenticated requests could use different Turn accounts to check contacts and send templated messages

1.4.0
------------
* TransferTo: keep a record of topup requests to transferto with TopupAttempt model
* TransferTo: start the participant on another rapidpro flow, if the request to TransferTo failed or was rejected in BuyAirtimeTakeAction task

1.3.2
------------
* Bug Fix: fix sentry setup which was not pulling through the env variable correctly

1.3.1
------------
* TransferTo: prevent BuyAirtimeTakeAction task from continuing if there is an error from TransferTo

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
