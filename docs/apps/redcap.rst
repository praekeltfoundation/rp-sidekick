#########
RP REDCAP
#########

ProjectCheck Task
=================

This task checks for incomplete surveys and notifies the survey participant by starting a flow in Rapidpro.

The task is started by doing a POST request on the `/redcap/start-project-check/<project-id>` endpoint.

The task will keep track of the values being changed by the survey participant.

PatientDataCheck Task
=====================

This task compares the patient records to the screening records for each day, and sends notifications to hospital leads and one more nominated person.

The hospital lead will captured a screening record for each week, the date is set to the Monday, this record is updated daily with the number of eligible cases that needs to be captured. This task will run daily and check if the patients captured on the previous day matches the number in the screening record for that day.

Each project will represent a country, with hospital split up by Data Access Groups on Redcap.

The task is started by doing a POST request on the `/redcap/start-patient-check/<project-id>` endpoint.

The task will keep track of the changes being made to the patient records.

The number of days included in the check is configured by the `REDCAP_HISTORICAL_DAYS` environment variable, the default is 3.