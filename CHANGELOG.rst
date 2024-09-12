VERSIONS
========

Next Release
------------

1.11.8
------------
msisdn_utils: An application that has small tools for handling phone numbers

1.11.7
------------
YAL: Fix redis connection

1.11.6
------------
YAL: Add page view caching

1.11.5
------------
YAL: Hardcode the get_content_search_term function.

1.11.4
------------
YAL: Add test day functionality

1.11.3
------------
YAL: Add contentset endpoint and fix field name bug

1.11.2
------------
YAL: Add clean fields function

1.11.1
------------
YAL: Add GetOrderedContentSet API

1.11.0
------------
Sidekick: Upgrade django to 4.2.11 and djangorestframework to 3.15.1
Added new randomisation app

1.10.6
------------
Sidekick: Bump django from 3.2.23 to 3.2.24

1.10.5
------------
Sidekick: Fix GroupMonitor __str__ function

1.10.4
------------
Sidekick: Add model to save group monitors

1.10.3
------------
Sidekick: Remove org_id from Rapidpro urls

1.10.2
------------
Sidekick: Add rapidpro flow start endpoint

1.10.1
------------
Sidekick: Multiple org fix for rapidpro group count monitor

1.10.0
------------
Sidekick: Added Rapdipro views for Turn
Sidekick: Add rapidpro group count monitor

1.9.4
------------
DTone: Fix airtime transfers for all networks

1.9.3
------------
DTone: Fix submit transaction body

1.9.2
------------
DTone: Fix submit transaction uuid

1.9.1
------------
DTone: Fix transaction serializer

1.9.0
------------
Added DTOne integration

1.8.9
------------
Sentry config for sample rate

1.8.8
------------
Upgrade redis library

1.8.7
------------
Interceptors: Handle empty events from WhatsApp

1.8.6
------------
Sidekick: Added threading to Dockerfile

1.8.5
------------
Interceptors: Handle no message or recipient_id in event

1.8.4
------------
Interceptors: Added a new app called rp_interceptors, which will accept inbound messages from WhatsApp and ensure that any status objects contain the recipient_id field before forwarding them.

1.8.3
------------
Sidekick: Django 3.2.18 and changed docker base image

1.8.2
------------
Sidekick: Django 3.2.14 and removed redcap dependancy

1.8.1
------------
Sidekick: Upgraded celery and libraries to latest versions

1.7.4
------------
Sidekick: Added an endpoint to get only contact uuids from the rapidpro API

1.7.3
------------
GP Connect: Automate file import by scanning the filesystem for new files
GP Connect: Move file storage to S3 and scan there for new files
GP Connect: Change to import csv rather than xlsx files
GP Connect: Small bugfixes

1.7.2
------------
Sidekick: Fix clean_message to not remove punctuation

1.7.1
------------
Sidekick: Allow space character to be submitted as variables to whatsapp template endpoint
GP Connect: Added a new Django app called rp_gpconnect to manage importing contacts from a xlsx file to RapidPro

1.7.0
------------
Recruit: Added a new Django app called rp_recruit, which will onboard users on to a RapidPro campaign from an external source. Currently only supports the WhatsApp channel.
Sidekick: Maintenance work on unpinning dev packages and using package ranges
Sidekick: Refactored tests to make better use of mocking
Sidekick: Created a test util function to investigate only some arguments of a mocked method

1.6.2
------------
Sidekick: Fix WA templated messsage send.

1.6.1
------------
Sidekick: Allow custom body for consent redirect
TransferTo: updated docs to better show how to use asynch endpoints.
Upgrade Django to >=2.2.2<2.3
Sidekick: Bugfix, reference last inbound message, not last message, for archiving Turn conversation

1.6.0
------------
Sidekick: Allow space character to be submitted as variables to whatsapp template endpoint
Sidekick: Add out-of-band consent feature for WhatsApp
Sidekick: Add feature for labelling the last received message in a Turn conversation
Sidekick: Add feature for archiving a Turn conversation

1.5.10
------------
Added isort
Add out-of-band consent for WhatsApp
ASOS: Updated documentation
ASOS: Refactoring group create and patient check task with retry strategy

1.5.9
------------
ASOS: Only update screening record timestamp if something actually changes
ASOS: Use correct redcap week key

1.5.8
------------
ASOS: Stop reminders when recruitment is over for hospitals.

1.5.7
------------
ASOS: Only include active hospitals in screening record check.

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
