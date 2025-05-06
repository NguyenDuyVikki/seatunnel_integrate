import uuid
from typing import Any, Dict, List, Union
from app.models.payload import SeaTunnelRequest, SourceConfig, AuthConfig, TableConfig
from pydantic import Field
from app.models.job import (
    Job,        
    JobConfig,
    SinkConfig,
    SftpSourceConfig,
    PostgreSQLSourceConfig,
    KafkaSinkConfig,
    IcebergSinkConfig,
    Environment,
    SourceType
)

def map_source_item(item: SourceConfig) -> Union[SftpSourceConfig, PostgreSQLSourceConfig]:
    plugin = item.source_type
    auth: AuthConfig  = item.auth
    tables: List[TableConfig] = item.tables
    cfg = item.config

    # common base
    base = {
        "plugin_name": plugin,
        # assume the first table name → plugin_output_table
        "plugin_output_table": "sample_table",
        "schema": None,
        "username": auth.username,
        "password": auth.password,
    }

    if plugin == SourceType.SFTP.value:
        return SftpSourceConfig(
            **base,
            host=cfg["host"],
            port=cfg["port"],
            file_path=cfg["file_path"],
            file_type=cfg["file_type"],
        )
# "source": [
#     {
#       "plugin_name": "Postgres-CDC",
#       "plugin_output": "users_cdc",
#       "username": "postgres",
#       "password": "postgres",
#       "decoding.plugin.name": "pgoutput",
#       "database-names": ["vikki_data"],
#       "schema-names": ["datalake"],
#       "table-names": ["vikki_data.datalake.person"],
#       "base-url": "jdbc:postgresql://host.docker.internal:5432/postgres?loggerLevel=OFF"
#     }
    elif plugin == SourceType.POSTGRESQLCDC.value:
        # build maps of name→schema for each table
        table_names = [
            (table.name)
            for table in tables
        ]
        schema_names = [
            (table.schema or {})
            for table in tables
        ]
            

        pg_conf = PostgreSQLSourceConfig(
            **base,
            host=cfg["host"],
            port=cfg["port"],
            database_names=table_names,
            schema_names=schema_names,
            table_names=table_names,
            base_url=auth.additional_params.get("base_url", ""),
        )
        print(f"pg_conf: {pg_conf=}")
        return pg_conf

    else:
        raise ValueError(f"Unsupported source_type {plugin!r}")


def map_sink_item(item: Dict[str, Any]) -> Union[KafkaSinkConfig, IcebergSinkConfig, SinkConfig]:
    plugin = item["sink_type"]
    auth   = item.get("auth", {})
    cfg    = item.get("config", {})

    base = {
        "plugin_name": plugin,
        # if you need auth in SinkConfig, add here
        **{},  
    }

    if plugin == "Kafka":
        return KafkaSinkConfig(
            **base,
            plugin_input_table = cfg.get("plugin_input_table", ""),
            topic              = cfg["topic"],
            source_table_name  = cfg["source_table_name"],
            bootstrap_servers  = cfg["bootstrap_servers"],
            partition          = cfg["partition"],
            data_format        = cfg["format"],                # renamed in your model
            schema_registry_url= cfg["schema.registry.url"],  # alias will pick up
            key_serializer     = cfg.get("key_serializer"),
            value_serializer   = cfg.get("value_serializer"),
        )

    elif plugin == "Iceberg":
        return IcebergSinkConfig(
            **base,
            table                   = cfg["table"],
            create_table_if_not_exists = cfg["create_table_if_not_exists"],
            iceberg_catalog_config  = cfg["iceberg.catalog.config"],
        )

    else:
        # fallback generic sink
        return SinkConfig(
            **base,
            **cfg
        )


def parse_job(request: SeaTunnelRequest ) -> Job:
    # 1) Environment (if any)
    # raw_env = request["env"]
    # if env:
    #     env = Environment(**raw_env)
    # else:
    #     env = None
    env = None

    # 2) Sources (wrap single→list if necessary)
    srcs = getattr(request, "source", None)
    if isinstance(srcs, SourceConfig):
        srcs = [srcs]
    source_confs = [map_source_item(s) for s in srcs]
    # 3) Sinks
    sinks = request.get("sink")
    if isinstance(sinks, dict):
        sinks = [sinks]
    sink_confs = [map_sink_item(s) for s in sinks]

    # 4) Build JobConfig + Job
    job_conf = JobConfig(env=env, source=source_confs, sink=sink_confs)
    return Job(
        id=str(uuid.uuid4()),
        name=request.get("job_name", "unnamed-job"),
        config=job_conf
    )
