#######
RP ASOS
#######

PatientDataCheck Task
=====================

This task compares the patient records to the screening records for each day, and sends notifications to hospital leads and one more nominated person.

The hospital lead will captured a screening record for each week, the date is set to the Monday, this record is updated daily with the number of eligible cases that needs to be captured. This task will run daily and check if the patients captured on the previous day matches the number in the screening record for that day.

Each project will represent a country, with hospital split up by Data Access Groups on Redcap.

The task is started by doing a POST request on the `/asos/start-patient-check/<project-id>` endpoint.

The task will keep track of the changes being made to the patient records.

The number of days included in the check is configured by the `ASOS_HISTORICAL_DAYS` environment variable, the default is 3.

Configuration
-------------

Hospital:
 * ``name`` The name of the hospital send to the RapidPro Flow.
 * ``data_access_group`` Used to filter records from Redcap.
 * ``rapidpro_flow`` UUID of the reminder flow that will get started in Rapidpro
 * ``hospital_lead_name`` Name of the hospital lead.
 * ``hospital_lead_urn`` URN where reminder will be sent.
 * ``nomination_name`` Name of second nominated person to receive reminder(Optional).
 * ``nomination_urn`` URN where second reminder will be sent(Optional).
