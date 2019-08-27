#############
RP GP Connect
#############
The main purpose of this app is to create and update RapidPro Contacts from the rows of an .xlsx file in an Amazon S3 bucket.

The column headers in the .xlsx file must all exist as Contact Fields in RapidPro, with the exception of `telephone_no` which will be extracted for the Contact URN.
An extra Contact Field named `has_whatsapp` must exist in RapidPro as well.

ContactImport Model
===================

This model stores the details for each import that has run.
 * ``file`` The .xlsx file that was imported.
 * ``org`` The Sidekick Organization instance to use for the RapidPro connection.
 * ``created_at`` The datetime that the instance was created.
 * ``created_by`` The User that the instance was created by (empty for instances created by the automated tasks).

Flow Model
==========

This model stores the information for the RapidPro Flows to start for imported Contacts.
 * ``type`` A string defining which Contacts should be started on this. Options are `new_contact` or `contact_update`.
 * ``rapidpro_flow`` A string containing the UUID of the Flow in Rapidpro.
 * ``org`` The Sidekick Organization that the Flow belongs to.

pull_new_import_file Task
=========================

This task will run hourly and is started by Celery Beat.

It checks the Amazon S3 bucket for a .xlsx file that does not exist in the ContactImports, downloads it and creates an instance for it.

The task will begin the import process by calling the `process_contact_import` task synchronously for the file being imported.

Only one new file will be imported per run.

process_contact_import Task
=========================

This task is run synchronously when a new file is found to be imported.

It loads the .xlsx file and calls the `import_or_update_contact` task asynchronously for each row in the file that has a `patients_tested_positive` value of `1`.

Each row is converted into a dict with the column headers as keys before calling the task.

import_or_update_contact Task
=========================

This task is run for each row in the file to be imported. It retrieves the whatsapp_id for the value in `telephone_no` and sets `has_whatsapp` to True if one exists or False if not.

If the Contact does not already exist in RapidPro it is created via the RapidPro API and started on the `new_contact` Flow for the Organization.

If the Contact does exist and has changed it is updated via the RapidPro API and started on the `contact_update` Flow for the Organization.

In both cases the dict of the row values is sent as the `extra` parameter when starting the flow.

If no Flow of the type exists for the Organization this task will raise an `ObjectDoesNotExist` error.

Configuration
-------------

These environment variables are required to be set for proper functioning:
 * ``AWS_ACCESS_KEY_ID`` Used to connect to the Amazon S3 bucket.
 * ``AWS_SECRET_ACCESS_KEY`` Used to connect to the Amazon S3 bucket.
 * ``AWS_STORAGE_BUCKET_NAME`` Used to connect to the Amazon S3 bucket.
 * ``GP_CONNECT_ORG_NAME`` The name of the Sidekick Organization that any imports will belong to (Optional. Defaults to "GP Connect").
 * ``GP_CONNECT_FILE_DIR`` The prefix to search for files in the Amazon S3 bucket (Optional. Defaults to "uploads/").


