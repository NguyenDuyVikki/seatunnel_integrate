import uuid
from typing import Any, Dict, List, Union, Optional
from app.models.payload import SeaTunnelRequest, SourceConfig, SinkConfig
from app.models.job import (
    Job,        
    CDCEnv,
    JobConfig,
    SeatunnelSourceConfig,
    SftpSourceConfig,
    PostgreSQLSourceConfig,
    KafkaSinkConfig,
    IcebergSinkConfig,
    SourceType
)
from pydantic import Field


def map_source_item(item: SourceConfig) -> Union[SftpSourceConfig, PostgreSQLSourceConfig]:
    plugin = item.source_type
    auth = item.auth
    cfg = item.config

    base = SeatunnelSourceConfig(
        plugin_name=plugin,
        plugin_output="sample_table",  # Example plugin output
        row_num=0,
        schema=None,
    )

    if plugin == SourceType.SFTP.value:
        return SftpSourceConfig(
            **base.dict(),
            host=cfg.get("host", "https:example.com"),
            port=cfg["port"],
            file_path=cfg["file_path"],
            file_type=cfg["file_type"],
        )

    elif plugin == SourceType.POSTGRESQLCDC.value:
        return PostgreSQLSourceConfig(
            **base.dict(),
            port=cfg.get("port", 5432),
            username=auth.username,
            password=auth.password,
            database_names=cfg.get("database-names", []),
            schema_names=cfg.get("schema-names", []),
            table_names=cfg.get("table-names", []),
            base_url=auth.additional_params.get("base-url", "") if auth.additional_params else "",
        )

    else:
        raise ValueError(f"Unsupported source_type {plugin!r}")


def map_sink_item(item: SinkConfig, source_table_name: List[str]) -> Union[KafkaSinkConfig, IcebergSinkConfig, SinkConfig]:
    plugin = item.sink_type
    auth = item.auth
    cfg = item.config

    if plugin == "Kafka":
        return KafkaSinkConfig(
            plugin_name="Kafka",  
            topic=cfg.get("topic", None),
            source_table_name=source_table_name,
            bootstrap_servers=cfg.get("bootstrap_servers", None),
            partition=cfg.get("partition", 1),
            format=cfg.get("format", "json"),
            schema_registry_url=cfg.get("schema_registry_url", None)
        )


    elif plugin == "Iceberg":
        return IcebergSinkConfig(
            plugin_name="Iceberg",  # Adding plugin_name here to match IcebergSinkConfig
            table=cfg["table"],
            create_table_if_not_exists=cfg.get("create_table_if_not_exists", False),
            iceberg_catalog_config=cfg.get("iceberg.catalog.config", {}),
        )

    # Fallback for other sink types
    print(f"Unknown sink type: {plugin}")
    return SinkConfig(plugin, **cfg)


def parse_job(request: SeaTunnelRequest) -> Job:
    # Handle Sources (wrap single → list if necessary)
    sources = [request.source] if isinstance(request.source, SourceConfig) else request.source
    source_confs = [map_source_item(s) for s in sources]
    
    # Handle Sinks
    sinks = [request.sink] if isinstance(request.sink, SinkConfig) else request.sink
    sink_confs = [map_sink_item(s, [source.plugin_output for source in source_confs]) for s in sinks]
    
    from app.models.job import Environment
    if request.source and request.source.source_type == "Postgres-CDC": 
        cdc_env = CDCEnv(
            execution_parallelism=1,
            job_mode="STREAMING",
            checkpoint_interval=5000,
            read_limit_bytes_per_second=7000000,
            read_limit_rows_per_second=400
    )

    
    # Build JobConfig + Job
    job_conf = JobConfig(env=cdc_env, source=source_confs, sink=sink_confs)
    return Job(
        jobId=str(uuid.uuid4()),
        jobName=getattr(request, "job_name", "unnamed-job"),
        config=job_conf
    )
