VERSIONS
========

Next Release
------------
* TransferTo: refactored task functionality into to take_action function - updates RapidPro fields and/or starts another flow
* TransferTo: add endpoint which purchases airtime, then updates RapidPro state with new take_action function

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
