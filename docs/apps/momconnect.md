# MomConnect App

The `momconnect` app is responsible for managing clinic-related operations and integrations within the project. It provides APIs and utilities to validate clinic codes and retrieve clinic details.

## Key Features

- **Clinic Management**: Handles the storage and retrieval of clinic information.
- **Validation**: Includes utilities to validate clinic codes.
- **API Endpoints**: Exposes endpoints for interacting with clinic data.

## Key Components

### Models
- **Clinic**: Represents a clinic with attributes such as `value` (clinic code) and `name`.

### Views
- **ClinicDetailsView**: API view to retrieve clinic details based on a provided clinic code.

### Utilities
- **validate_clinic_code**: Utility function to validate the format of a clinic code.

## API Endpoints

### Clinic Details
- **Endpoint**: `/api/clinic-details/`
- **Method**: `GET`
- **Parameters**:
  - `clinic_code` (required): The code of the clinic to retrieve.
- **Responses**:
  - `200 OK`: Returns the clinic details.
  - `400 Bad Request`: Missing or invalid clinic code.
  - `404 Not Found`: Clinic not found.

## Testing

The `momconnect` app includes comprehensive test coverage for its views and utilities. Tests are located in `momconnect/tests/`.

## Usage

1. Ensure the `momconnect` app is included in the `INSTALLED_APPS` setting of your Django project.
2. Use the provided API endpoints to interact with clinic data.
3. Refer to the test cases for examples of how to use the app's features programmatically.
