# **TURN ALERTS README**

#

# About

The Turn Alerts app is a bridge between sidekick and Turn. It acts as a listener for events and messages sent by Turn, allowing us to both monitor and react to them in real-time.

**What it does:**

- Receives and Processes Turn Webhooks:
  - Handles incoming messages and events from Turn via HTTP POST requests.
  - Validates the authenticity of each request using a secret key (Turn hmac signature headers etc).
  - Extracts relevant information from the webhook payload, such as message type, direction, status, and error codes.
- Triggers Turn Journeys:
  - Based on predefined configurations, it initiates specific actions such as starting Turn journeys when certain error codes are encountered.
- Monitors and Logs Events:
  - Utilizes Prometheus to track key metrics, such as message volume, error rates, and journey initiation counts.
  - Provides valuable insights into the performance and behavior of the Turn integration. We can visualize this in any of the grafana instances if the organization (ex, the ndoh one)

# Installation

1. Create a Virtual Env
    1. python3 -m venv .venv
    2. source .venv/bin/activate
2. Activate Virtual environment
    1. virtualenv -p python3 .venv
    2. source .venv/bin/activate
3. Install dependencies
    1. pip install -r requirements.txt
4. Install dev dependencies
    1. pip install -r requirements-dev.txt
5. Create django superuser
    1. python manage.py createsuperuser
    2. Follow the prompts to create a username, email, and password for the superuser account. You'll need this information to access the Django admin panel.
6. Run the development server and access turnalerts admin
    1. python manage.py runserver
    2. <http://127.0.0.1:8000/admin/>

# Configuration

1. Create a TurnSecret model instance for each organization that will use the Turn Alerts Layer.
    1. The org field should be a reference to the corresponding Organization model instance.
    2. The secret field should be set to the Turn secret associated with the organization.
2. Create TurnActions model instances to define how the Turn Alerts Layer should respond to specific error codes.
    1. The org field should be a reference to the corresponding Organization model instance.
    2. The journey_id field should be set to the ID of the Turn journey that you want to start when the corresponding error code is encountered.
    3. The error_code field should be set to the Turn error code that triggers the journey start.

# Usage

The Turn Alerts Layer exposes a single Django view:

turnalerts.TurnAlertsLayerView

This view expects POST requests to be sent to the following URL pattern:

turnalerts/turn-messages/org_id/turn_secret_id/

org_id is the ID of the organization that is sending the request.

turn_secret_id is the ID of the TurnSecret model instance that corresponds to the organization.

The request body should be a JSON object that conforms to the Turn message or event schema.

The Turn Alerts Layer will validate the request signature and then process the message or event data.

For WhatsApp webhook type, the Turn Alerts Layer will increment prometheus counters for the message type, direction, and fallback channel.

For Turn events, the Turn Alerts Layer will increment prometheus counters for the message status, error code (if present), and fallback channel.

If a TurnActions model instance exists for the encountered error code, the Turn Alerts Layer will start the corresponding Turn journey using the configured organization's Engage URL and token.

# Additional Notes

The Turn Alerts Layer uses Prometheus counters to track message and event data. You can configure Grafana (ndoh instance or otherwise) to scrape these counters to monitor the activity of the Turn Alerts Layer.

The Turn Alerts Layer uses Celery tasks to start Turn journeys asynchronously.
