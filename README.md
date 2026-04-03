# Temperature Measurements REST Service

A Python REST API service for receiving and managing temperature measurements from multiple sensors.

## Features

- **POST /api/measurements** - Submit a single temperature measurement (authenticated)
- **POST /api/measurements/batch** - Submit a batch of temperature measurements (authenticated)
- **GET /api/measurements** - Retrieve all stored measurements (authenticated)
- **GET /api/measurements/day/{date}** - Retrieve all measurements for a specific day grouped by sensor address (authenticated)
- **GET /api/measurements/{sensor_address}** - Retrieve measurements for a specific sensor (authenticated)
- **DELETE /api/measurements** - Clear all measurements (authenticated)
- **GET /** - Health check endpoint (no authentication required)

## Useful DB Snippets

```
docker exec -it <sha> /bin/bash
psql -U hsmuser -d hsm

select count(*) from temperature_measurements;
select * from temperature_measurements order by timestamp desc limit 15;
select * from sensors;
```

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

