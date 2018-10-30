#########
RP REDCAP
#########

ProjectCheck Task
=================

This task checks for incomplete surveys and notifies the survey participant by starting a flow in Rapidpro.

The task is started by doing a POST request on the `/redcap/start-project-check/<project-id>` endpoint.

The task will keep track of the values being changed by the survey participant.
