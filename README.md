# Temperature Measurements REST Service

A Python REST API service for receiving and managing temperature measurements from multiple sensors.

## Features

- **POST /api/measurements** - Submit a list of temperature measurements (authenticated)
- **GET /api/measurements** - Retrieve all stored measurements (authenticated)
- **GET /api/measurements/{sensor_address}** - Retrieve measurements for a specific sensor (authenticated)
- **DELETE /api/measurements** - Clear all measurements (authenticated)
- **GET /** - Health check endpoint (no authentication required)

## Authentication

All API endpoints under `/api/` are protected with **HTTP Basic Authentication**.

**IMPORTANT:** Credentials **must** be provided via a mounted secret file. A `./secrets` directory with `api_username` and `api_password` files is included for development (containing `admin/admin`). For production, replace these files with your own credentials.

### Secure Credential Management

Credentials are always loaded from mounted secret files—either Docker Secrets or volume-mounted files.

#### For Development (using default admin/admin)

The repository includes a `./secrets` directory with default credentials:
- `./secrets/api_username` → `admin`
- `./secrets/api_password` → `admin`

When you run `docker compose up`, this directory is automatically mounted to `/app/secrets` in the container.

```bash
docker compose up -d
```

Then test with:

```bash
curl -u admin:admin http://localhost:8000/api/measurements
```

#### For Production (using your own secrets)

**Step 1:** Replace the default credentials

```bash
echo "prod_username" > secrets/api_username
echo "prod_secure_password" > secrets/api_password
chmod 400 secrets/*
```

**Step 2:** Deploy with the updated secrets

- **Docker Compose:** Mount the updated `./secrets` directory as shown above
- **Kubernetes:** Use secret ConfigMaps mounted at `/app/secrets`

### Making Authenticated Requests

#### Using cURL
```bash
curl -u myuser:mypassword http://localhost:8000/api/measurements
```

#### Using Python requests
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'http://localhost:8000/api/measurements',
    auth=HTTPBasicAuth('myuser', 'mypassword')
)
```

#### Using JavaScript/Fetch
```javascript
const username = 'myuser';
const password = 'mypassword';
const credentials = btoa(`${username}:${password}`);

fetch('http://localhost:8000/api/measurements', {
  headers: {
    'Authorization': `Basic ${credentials}`
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## Project Structure

```
hsm-backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # Pydantic data models
│   └── auth.py              # Authentication logic (secure credential handling)
├── secrets/                 # Credentials storage (git-ignored)
│   ├── api_username         # Username file
│   └── api_password         # Password file
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-container orchestration
├── .dockerignore             # Docker build context exclusions
├── generate-secrets.sh      # Script to generate secret files
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /workspaces/hsm-backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Service

Start the REST service with Uvicorn:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`

- Interactive API documentation: `http://localhost:8000/docs`
- Alternative documentation: `http://localhost:8000/redoc`

## Docker Setup

### Building the Docker Image

Build the Docker image using the provided Dockerfile:

```bash
docker build -t temperature-service:latest .
```

Or with a specific tag:

```bash
docker build -t temperature-service:1.0.0 .
```

### Running the Docker Container

#### Basic Usage

Run the container with default settings:

```bash
docker run -p 8000:8000 temperature-service:latest
```

The service will be available at `http://localhost:8000`

#### With Custom Port

Map to a different port on your host:

```bash
docker run -p 9000:8000 temperature-service:latest
```

Access the service at `http://localhost:9000`

#### Running in Background

Run the container in detached mode:

```bash
docker run -d -p 8000:8000 --name temp-service temperature-service:latest
```

To view logs:
```bash
docker logs temp-service
```

To follow logs in real-time:
```bash
docker logs -f temp-service
```

#### Stopping and Removing the Container

Stop the container:
```bash
docker stop temp-service
```

Remove the container:
```bash
docker rm temp-service
```

<!-- section removed: no environment variable credential support -->

#### Advanced Usage with Volume Mounting

Mount a local directory for data persistence (if database is implemented):

```bash
docker run -d \
  -p 8000:8000 \
  -v /path/to/local/data:/app/data \
  --name temp-service \
  temperature-service:latest
```

### Docker Compose

Alternatively, use Docker Compose for easier management. The included `docker-compose.yml` already mounts the credentials directory:

```yaml
version: '3.8'

services:
  temperature-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    container_name: temperature-service
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    volumes:
      - ./app:/app/app
      - ./secrets:/app/secrets:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

Then run with:

```bash
docker-compose up -d
```

To view logs:
```bash
docker-compose logs -f
```

To stop and cleanup:
```bash
docker-compose down
```

### Checking Container Health

View container status:
```bash
docker ps
```

Inspect container details:
```bash
docker inspect temperature-service
```

### Publishing to Docker Registry

Tag the image for a registry:

```bash
docker tag temperature-service:latest your-registry/temperature-service:latest
```

Push to registry:

```bash
docker push your-registry/temperature-service:latest
```

Pull from registry:

```bash
docker pull your-registry/temperature-service:latest
```

### Common Issues and Solutions

**Port already in use:**
```bash
docker run -p 8001:8000 temperature-service:latest
```

**Container exits immediately:**
Check logs with: `docker logs <container_id>`

**Permission denied errors:**
Run Docker commands with sudo if necessary, or add your user to the docker group.

## API Endpoints

### 1. Submit Temperature Measurements
**POST** `/api/measurements`

Request body:
```json
{
  "measurements": [
    {
      "sensorAddress": "sensor-001",
      "temperature": 22.5,
      "timestamp": "2026-02-28T10:30:00"
    },
    {
      "sensorAddress": "sensor-002",
      "temperature": 18.3,
      "timestamp": "2026-02-28T10:30:01"
    }
  ]
}
```

Response:
```json
{
  "success": true,
  "message": "Successfully received 2 temperature measurement(s)",
  "measurements_received": 2
}
```

### 2. Get All Measurements
**GET** `/api/measurements`

Response:
```json
[
  {
    "sensorAddress": "sensor-001",
    "temperature": 22.5,
    "timestamp": "2026-02-28T10:30:00"
  },
  {
    "sensorAddress": "sensor-002",
    "temperature": 18.3,
    "timestamp": "2026-02-28T10:30:01"
  }
]
```

### 3. Get Measurements for Specific Sensor
**GET** `/api/measurements/{sensor_address}`

Example: `GET /api/measurements/sensor-001`

Response:
```json
{
  "sensor_address": "sensor-001",
  "data": [
    {
      "sensorAddress": "sensor-001",
      "temperature": 22.5,
      "timestamp": "2026-02-28T10:30:00"
    }
  ]
}
```

### 4. Clear All Measurements
**DELETE** `/api/measurements`

Response:
```json
{
  "message": "Cleared 2 measurements"
}
```

### 5. Health Check
**GET** `/`

Response:
```json
{
  "service": "Temperature Measurements Service",
  "status": "running",
  "version": "1.0.0"
}
```

## Data Models

### TemperatureMeasurement
- **sensorAddress** (str, required): Unique identifier for the sensor
- **temperature** (float, required): Temperature value in Celsius
- **timestamp** (datetime, required): ISO 8601 format

### TemperatureMeasurementRequest
- **measurements** (List[TemperatureMeasurement], required): Array of temperature measurements

### TemperatureMeasurementResponse
- **success** (bool): Operation status
- **message** (str): Descriptive message
- **measurements_received** (int): Count of measurements processed

## Example Usage with cURL

```bash
# Health check (no authentication required)
curl http://localhost:8000/

# Submit measurements (with authentication)
curl -u admin:admin -X POST http://localhost:8000/api/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "measurements": [
      {"sensorAddress": "sensor-001", "temperature": 22.5, "timestamp": "2026-02-28T10:30:00"},
      {"sensorAddress": "sensor-002", "temperature": 18.3, "timestamp": "2026-02-28T10:30:01"}
    ]
  }'

# Get all measurements (with authentication)
curl -u admin:admin http://localhost:8000/api/measurements

# Get measurements for specific sensor (with authentication)
curl -u admin:admin http://localhost:8000/api/measurements/sensor-001

# Clear measurements (with authentication)
curl -u admin:admin -X DELETE http://localhost:8000/api/measurements
```

## Beispiel: Sensor anlegen per curl

```bash
curl -u admin:admin -X POST \
  http://localhost:8000/api/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensorAddress": "28-00000a1b2c3d",
    "active": true,
    "color": "#ff0000",
    "name": "Keller Sensor",
    "groupName": "Keller"
  }'
```

## Technologies Used

- **FastAPI** - Modern Python web framework for building APIs
- **Uvicorn** - ASGI web server implementation
- **Pydantic** - Data validation using Python type annotations

## Development

To run in development mode with auto-reload:
```bash
uvicorn app.main:app --reload
```

To run with specific host and port:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Notes

- Current implementation uses in-memory storage (measurements are lost when the service restarts)
- For production use, integrate with a database (PostgreSQL, MongoDB, etc.)
- Consider adding authentication/authorization for production deployment
- Add rate limiting for protection against abuse
- Implement proper error logging and monitoring

## License

MIT