# seatunnel-demo
A FastAPI project for demonstration purposes.

## Installation

```bash
brew install poetry
poetry install
```

## Usage

### Start the API Server

```bash
cd seatunnel_integrate
python -B main.py
```

### Test API

Open Swagger UI at http://localhost:8000/swagger
/api/v1/jobs
#### Example Payload

```json
{
  "source": {
    "source_type": "Postgres-CDC",         
    "auth": {
      "username": "postgres",
      "password": "postgres",
      "additional_params": {
        "base-url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
      }
    },
    "config": {
      "host": "host.docker.internal",
      "table-names": ["vikki_data.datalake.person"],
      "port": 5432,
      "database-names": ["vikki_data"],
      "schema-names": ["datalake"]
    }
  },
  "sink": {
    "sink_type": "Kafka",
    "auth": {
      "username": "kafka_user",
      "password": "kafka_password",
      "additional_params": {}
    },
    "config": {
      "bootstrap_servers": "kafka:9092",
      "topic": "users_cdc",
      "format": "json",
      "schema_registry_url": "http://schema-registry:8081"
    }
  }
}
```

Make a POST request to `/api/v1/jobs` with the above payload to create a new job.


