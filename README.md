# Tenant Electricity Management API

A Django REST API for managing tenant electricity bills and connection statuses.

## Table of Contents

- [Overview](#overview)
- [API Endpoints](#api-endpoints)
  - [Latest Bills](#latest-bills)
  - [Connection Status](#connection-status)
  - [Update Connection Status](#update-connection-status)
- [Request & Response Examples](#request--response-examples)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)

## Overview

This API provides functionality for managing tenant electricity bills and connection statuses. It allows you to:

- Retrieve the latest electricity bills for multiple tenants
- Check connection status for multiple tenants
- Update the connection status for a tenant

## API Endpoints

### Latest Bills

Retrieve the latest bill details for multiple tenants.

- **URL**: `/bill/latest/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "tenants": [
    {
      "tenant_index": 0,
      "product_id": "1112"
    },
    {
      "tenant_index": 1,
      "product_id": "1113"
    },
    {
      "tenant_index": 2,
      "product_id": "1114"
    }
  ]
}
```
- **Response**:
```json
{
  "tenants": [
    {
      "tenant_index": 0,
      "product_id": "1112",
      "bill_details": {
        "month": "2025-02",
        "amount": 11900,
        "kw_value": 337.7,
        "status": "not_paid",
        "payment_date": null,
        "calculated_at": "2025-03-01T00:01:00.119374+05:30"
      }
    },
    {
      "tenant_index": 1,
      "product_id": "1113",
      "bill_details": {
        "month": "2025-02",
        "amount": 11900,
        "kw_value": 333.51,
        "status": "not_paid",
        "payment_date": null,
        "calculated_at": "2025-03-01T00:01:00.119374+05:30"
      }
    },
    {
      "tenant_index": 2,
      "product_id": "1114",
      "bill_details": {
        "month": "2025-02",
        "amount": 11900,
        "kw_value": 337.7,
        "status": "not_paid",
        "payment_date": null,
        "calculated_at": "2025-03-01T00:01:00.119374+05:30"
      }
    }
  ]
}
```

### Connection Status

Check the electricity connection status for multiple tenants.

- **URL**: `/electricity/connection-status/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "tenants": [
    {
      "tenant_index": 0,
      "product_id": "1112"
    },
    {
      "tenant_index": 1,
      "product_id": "1113"
    },
    {
      "tenant_index": 2,
      "product_id": "1113"
    }
  ]
}
```
- **Response**:
```json
{
  "tenants": [
    {
      "tenant_index": 0,
      "connection_status": false
    },
    {
      "tenant_index": 1,
      "connection_status": true
    },
    {
      "tenant_index": 2,
      "connection_status": true
    }
  ]
}
```

### Update Connection Status

Update the electricity connection status for a tenant.

- **URL**: `/electricity/update-connection-status/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "connection_status": true,
  "product_id": "1113"
}
```
- **Response**:
```json
{
  "message": "Connection Status of 1113 updated to True successfully"
}
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tenant-electricity-api.git
   cd tenant-electricity-api
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure database settings in `settings.py`

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

### Example: Retrieving Latest Bills

```python
import requests
import json

url = "http://localhost:8000/bill/latest/"
payload = {
  "tenants": [
    {"tenant_index": 0, "product_id": "1112"},
    {"tenant_index": 1, "product_id": "1113"}
  ]
}
headers = {
  'Content-Type': 'application/json'
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

### Example: Updating Connection Status

```python
import requests
import json

url = "http://localhost:8000/electricity/update-connection-status/"
payload = {
  "connection_status": false,
  "product_id": "1112"
}
headers = {
  'Content-Type': 'application/json'
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

## Development

### Prerequisites

- Python 3.8+
- Django 4.0+
- Django REST Framework 3.13+

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

[MIT License](LICENSE)
