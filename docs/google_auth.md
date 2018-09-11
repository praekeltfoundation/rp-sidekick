# Authenticating RP Sidekick to use Google APIs

Some of the django apps within RP Sidekick use Google APIs. This requires some additional set up, which is basically the same for both dev and production environments.

In order to set up Google services, you will need to
1. Log in to your Google account and navigate to the [developer console](https://console.developers.google.com/apis/dashboard).
1. Select the organization that the application will fall under. If you are using a local dev environment, this does not matter much. If this is related to your company or organisation, make sure that you create the application under their organization, so that other devs have access to, and can update where necessary.
1. With the correct organization, create a new project with the appropriate name (try and include details like dev/qa/prod and other relevant information).
1. Within this new project, search for and add the services that you would like the application to use - at this point in time, Sidekick only requires read approvals for spreadsheets, but this will probably include other services in the future.
1. Create credentials for a web application. Note that Google requires a callback path, which you will need to give it. In this case, it will be `https://YOUR.URL.ORG/oauth2callback/`.
If you are working in a dev environment, you can provide it with a local path, e.g. `http://localhost:8000/oauth2callback/`.
1. You will then be able to download a JSON file, usually called `client_id_.json`, with the credentials. Take the following values from the file:
    ```
    {
        "web": {
            "client_id": "fakeclientid",
            "project_id": "fakeprojectid",
            ...
            "client_secret": "fakeclientsecret",
            ...
        },
        ...
    }
    ```
    and place those values in the root `.env` file or add them to the build configuration as environment variables as follows:
    ```
    GOOGLE_CLIENT_ID=fakeclientid
    GOOGLE_PROJECT_ID=fakeprojectid
    GOOGLE_CLIENT_SECRET=fakeclientsecret
    ```
    Then delete the `client_id_.json` file.
    WARNING: DO NOT COMMIT THIS FILE TO VERSION CONTROL.
1. Your application should now be authentiacted to Google and should function as intended. However, if you are running this in a local environment, without SSL (i.e. you can only serve webpages over `http` and not `https`) then you will need to run the following in the terminal window in which you run the server:
    ```
    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    ```
    Alternatively, if you only want this environment variable enabled while the server is running, you can run the following:
    ```
    $ OAUTHLIB_INSECURE_TRANSPORT=1 python manage.py runserver
    ```

## Document TODOs:
- TODO: provide examples of how to check that authentication is working from a db level and maybe write a checking script.
- TODO: Add GIFs showing how to
