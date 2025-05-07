from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import uuid

class SourceType(str, Enum):
    POSTGRESQLCDC = "Postgres-CDC"
    SFTP = "SFTP"
    KAFKA = "Kafka"

class Environment(BaseModel):
    job_mode: str = Field(default="BATCH", alias="job.mode")
    parallelism: int = Field(default=1, ge=1)

    class Config:
        populate_by_name = True

class CDCEnv(BaseModel):
    execution_parallelism: int = Field(1, alias="execution.parallelism")
    job_mode: str = Field("STREAMING", alias="job.mode")
    checkpoint_interval: int = Field(5000, alias="checkpoint.interval")
    read_limit_bytes_per_second: int = Field(7000000, alias="read_limit.bytes_per_second")
    read_limit_rows_per_second: int = Field(400, alias="read_limit.rows_per_second")
    
    class Config:
        allow_population_by_field_name = True  

class SeatunnelSourceConfig(BaseModel):
    plugin_name: str
    plugin_output: str
    schema_: Optional[Dict[str, Any]] = Field(None, alias="schema")

    class Config:
        populate_by_name = True

class SftpSourceConfig(SeatunnelSourceConfig):
    host: str
    port: int = Field(ge=1, le=65535)
    username: str
    password: str
    file_path: str
    file_type: str

class PostgreSQLSourceConfig(SeatunnelSourceConfig):
    port: Optional[int] = Field(None, ge=1, le=65535)  
    username: Optional[str] = None
    password: Optional[str] = None
    database_names: Optional[List[str]] = Field(None, alias="database-names")         
    schema_names: Optional[List[str]] = Field(None, alias="schema-names")   
    table_names: Optional[List[str]] = Field(None, alias="table-names")       
    base_url: Optional[str] = Field(None, alias="base-url")       
    decoding_plugin_name: str = Field("pgoutput", alias="decoding.plugin.name")
    class Config:
        extra = 'allow'



      

class KafkaSinkConfig(BaseModel):
    plugin_name: Optional[str] = "Kafka"
    topic: str
    source_table_name: List[str]
    bootstrap_servers: str = Field("kafka:9092", alias="bootstrap.servers")  
    partition: int
    format: str
    schema_registry_url: str = Field("http://schema-registry:8081", alias="schema.registry.url") 
    
class IcebergSinkConfig(BaseModel):
    plugin_name: str
    plugin_input_table: str
    catalog_name: Optional[str] = None
    catalog_type: Optional[str] = None
    namespace: Optional[str] = None
    table: Optional[str] = None
    create_table_if_not_exists: Optional[str] = None
    table: str
    create_table_if_not_exists: str
    iceberg_catalog_config: Dict[str, str] = Field(alias="iceberg.catalog.config")

    class Config:
        populate_by_name = True

class JobConfig(BaseModel):
    env: Optional[Union[Environment, CDCEnv]] = None
    source: List[Union[SftpSourceConfig, PostgreSQLSourceConfig]]
    sink: List[Union[KafkaSinkConfig, IcebergSinkConfig]]

    @validator('source')
    def validate_source_types(cls, sources):
        for source in sources:
            if source.plugin_name not in SourceType.__members__.values():
                raise ValueError(f"Invalid source type: {source.plugin_name}")
        return sources

class Job(BaseModel):
    jobId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jobName: str
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
def create_source_config(data: Dict[str, Any]) -> SeatunnelSourceConfig:
    source_type = data.get('plugin_name')
    if source_type == SourceType.SFTP.value:
        return SftpSourceConfig(**data)
    elif source_type == SourceType.POSTGRESQLCDC.value:
        return PostgreSQLSourceConfig(**data)
    raise ValueError(f"Unsupported source type: {source_type}")

# Factory for dynamic sink config creation
def create_sink_config(data: Dict[str, Any]) -> IcebergSinkConfig:
    if 'iceberg.catalog.config' in data:
        return IcebergSinkConfig(**data)
    return IcebergSinkConfig(**data)