#######
RP ASOS
#######

PatientDataCheck Task
=====================

This task will run daily, it sends a small summary of the screening records and the CRFs for each day to the hospital leads and one more nominated person.

The hospital lead will capture daily counts in the screening record, the date is set to when the hospital starts recruiting, this record is updated daily with the number of eligible cases that needs to be captured.

Each project will represent a country, with hospital split up by Data Access Groups on Redcap.

The task is started by doing a POST request on the `/asos/start-patient-check/<project-id>/<tz-code>` endpoint.

The task will keep track of the changes being made to the patient and screening records.

CreateHospitalGroups Task
=========================

This task runs daily before the PatientDataCheck task. It creates a WhatsApp group per hospital and invites the hospital lead and other notminated person.

Once they join the task will update them to admin on the next run.

ScreeningRecordCheck Task
=========================

This task also runs daily 12pm SAST. It checks for screening records from active hospitals that have not been updated in the last 24h and sends a notification to the steering committee WhatsApp group.

The WhatsApp group ID is configure by the `ASOS_ADMIN_GROUP_ID` environment variable.

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
 * ``whatsapp_group_id`` This will be populated by the CreateHospitalGroups task with the group created for this hospital.
 * ``tz_code`` Timezone code used to send reminders based on the local time.
 * ``is_active`` Active flag to disable a hospital, the PatientDataCheck will disable a hospital if they have completed their recruitment.

Notes
-----

All tasks are started by triggers configured in Rapidpro, which starts a flow thats calls a Sidekick webhook.

Webhook failures will trigger an alert from Redash for further investigation.

