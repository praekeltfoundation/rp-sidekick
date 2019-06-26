# Recruit

This app serves as a means of recruiting individuals to be contacted via WhatsApp (and by extension RapidPro), through an online signup service.

The indivdual lands on a particular recruitment campaign, supplies their MSISDN and a name, and they are re-directed to a success screen, assuming all has gone well, supplying them with a pin. They should then be started on a flow that requests the pin for identity confirmation.

## Notes
* this currently only supports WhatsApp, but could be adjusted to support SMS and other RapidPro channels as well

## Set Up
To Set up a Recruitment Campaign, make sure you have already created an Organization, and have the following created on the RapidPro instance that you want to use:

- a recruitment flow that you can begin the contact on, and this flow's UUID
- a group that you wish to add this group to and the group name (note that this might change in the future, where the contact might only be added to a group once they have supplied the pin)
- have created a RapidPro contact field that you can store the pin value that they are given, against and have that field's key (not the same thing as the contact field's name)

Use this info to create the Recruitment object, which can be accessed via the Django admin under 'rp_recruitment'. The object will automatically be given a UUID. This is used in the URL to refer to the particular campaign you wish to run. For example, if your Recruitment Campaign is given a UUID of `91e10004-0af4-453c-9840-79695b48aef4`, then users shoudl be directed to `https:your.url/recruit/91e10004-0af4-453c-9840-79695b48aef4`. Once the user successfully submits valid data, the contact has been created and flow started, they are redirected to a success screen which directs them to their next actions.
