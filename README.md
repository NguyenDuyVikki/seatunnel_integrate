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
    "source_type": "PostgreSQL",
    "auth": {
      "username": "postgres",
      "password": "postgres",
      "additional_params": {
        "base_url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
      }
    },
    "tables": [
      {
        "name": "person",
        "schema": {"id": "int", "name": "string"}
      }
    ],
    "config": {
      "host": "host.docker.internal",
      "port": 5432,
      "decoding.plugin.name": "pgoutput",
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
      "source_table_name": ["person"],
      "partition": 1,
      "format": "json",
      "schema.registry.url": "http://schema-registry:8081"
    }
  }
}
```

Make a POST request to `/api/v1/jobs` with the above payload to create a new job.


