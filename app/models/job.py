from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import uuid
# "sink": [
#       {
#         "plugin_name": "Iceberg",
#         "plugin_input_table": "raw_data",
#         "catalog_name": "glue_catalog",
#         "catalog_type": "glue",
#         "namespace": "demo_glue_duy",
#         "table": "seatunnel",
#         "create_table_if_not_exists": "true",
#         "iceberg.catalog.config": {
#           "warehouse":      "s3://demo-seatunnel/",
#           "catalog-impl":   "org.apache.iceberg.aws.glue.GlueCatalog",
#           "io-impl":        "org.apache.iceberg.aws.s3.S3FileIO",
#           "client.region":  "ap-southeast-1"
#         }
#       }
      
# "sink": [
#     {
#       "plugin_name": "Kafka",
#       "source_table_name": ["users_cdc"],
#       "bootstrap.servers": "kafka:9092",
#       "topic": "person_cdc",
#       "format": "json",
#       "schema.registry.url": "http://schema-registry:8081"
#     }
#   ]
class SourceType(str, Enum):
    POSTGRESQLCDC = "PostgreSQL"
    SFTP = "SFTP"
    KAFKA = "Kafka"

class Environment(BaseModel):
    job_mode: str = Field(default="BATCH", alias="job.mode")
    parallelism: int = Field(default=1, ge=1)

    class Config:
        populate_by_name = True

class SourceConfig(BaseModel):
    plugin_name: str
    plugin_output_table: str
    row_num: Optional[int] = None
    schema_: Optional[Dict[str, Any]] = Field(None, alias="schema")

    class Config:
        populate_by_name = True

class SftpSourceConfig(SourceConfig):
    host: str
    port: int = Field(ge=1, le=65535)
    username: str
    password: str
    file_path: str
    file_type: str

class PostgreSQLSourceConfig(SourceConfig):
    host: str
    port: int = Field(ge=1, le=65535)
    username: str
    password: str
    database_names: Dict[str, Any]
    schema_names: Dict[str, Any]
    table_names: Dict[str, Any]
    base_url: str

class SinkConfig(BaseModel):
    plugin_name: str
    plugin_input_table: str
    catalog_name: Optional[str] = None
    catalog_type: Optional[str] = None
    namespace: Optional[str] = None
    table: Optional[str] = None
    create_table_if_not_exists: Optional[str] = None

      

class KafkaSinkConfig(SinkConfig):
    topic: str
    source_table_name: List[str]
    bootstrap_servers: str
    partition: int
    topic: str
    format: str
    schema_registry_url: str
    key_serializer: Optional[str] = None
    value_serializer: Optional[str] = None
    
class IcebergSinkConfig(SinkConfig):
    table: str
    create_table_if_not_exists: str
    iceberg_catalog_config: Dict[str, str] = Field(alias="iceberg.catalog.config")

    class Config:
        populate_by_name = True

class JobConfig(BaseModel):
    env: Environment
    source: List[Union[SftpSourceConfig, PostgreSQLSourceConfig]]
    sink: List[Union[SinkConfig, IcebergSinkConfig]]

    @validator('source')
    def validate_source_types(cls, sources):
        for source in sources:
            if source.plugin_name not in SourceType.__members__.values():
                raise ValueError(f"Invalid source type: {source.plugin_name}")
        return sources

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    config: JobConfig
    status: Optional[str] = None

    class Config:
        json_encoders = {
            uuid.UUID: str
        }

class JobResponse(BaseModel):
    """Response model for job creation and status endpoints"""
    job_id: str
    status: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[str] = None

# Factory for dynamic source config creation
def create_source_config(data: Dict[str, Any]) -> SourceConfig:
    source_type = data.get('plugin_name')
    if source_type == SourceType.SFTP.value:
        return SftpSourceConfig(**data)
    elif source_type == SourceType.POSTGRESQLCDC.value:
        return PostgreSQLSourceConfig(**data)
    raise ValueError(f"Unsupported source type: {source_type}")

# Factory for dynamic sink config creation
def create_sink_config(data: Dict[str, Any]) -> SinkConfig:
    if 'iceberg.catalog.config' in data:
        return IcebergSinkConfig(**data)
    return SinkConfig(**data)