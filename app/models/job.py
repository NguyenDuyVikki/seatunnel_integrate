from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class Environment(BaseModel):
    job_mode: str = Field(default="BATCH", alias="job.mode")
    parallelism: int = 1

class SourceConfig(BaseModel):
    plugin_name: str
    plugin_output_table: str
    row_num: Optional[int] = None
    schema_: Optional[Dict[str, Any]] = Field(None, alias="schema")

class IcebergConfig(BaseModel):
    catalog_name: str
    catalog_type: str
    namespace: str
    table: str
    create_table_if_not_exists: str
    iceberg_catalog_config: Dict[str, str] = Field(alias="iceberg.catalog.config")

class SinkConfig(BaseModel):
    plugin_name: str
    plugin_input_table: str
    catalog_name: Optional[str] = None
    catalog_type: Optional[str] = None
    namespace: Optional[str] = None
    table: Optional[str] = None
    create_table_if_not_exists: Optional[str] = None
    iceberg_catalog_config: Optional[Dict[str, str]] = Field(default=None, alias="iceberg.catalog.config")

class JobConfig(BaseModel):
    env: Environment
    source: List[SourceConfig]
    sink: List[SinkConfig]

class Job(BaseModel):
    id: Optional[str] = None
    name: str
    config: JobConfig
    status: Optional[str] = None

class JobResponse(BaseModel):
    """Response model for job creation and status endpoints"""
    job_id: str
    status: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[str] = None