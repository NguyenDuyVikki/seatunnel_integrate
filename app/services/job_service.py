from app.client.http_client import SeaTunnelClient
from app.models.job import Job, JobResponse, JobConfig
from typing import Dict, Any, Optional
from app.utils.db_connector import SchemaManager, DBConfig, PostgreSQLConnector
from typing import List

class JobService:
    def __init__(self, client: SeaTunnelClient):
        self.client = client
        
    async def mapper_schema(self, schema: Dict[str, Any], primary_keys: List[str] = None) -> Dict[str, Any]:
        schema_manager = SchemaManager()
        pg_config = DBConfig(
        host="localhost",
        port=5432,
        username="db_cluster_viewer",
        password="qfxu4dUDHZlJ",
        database="account",
        pool_min=2,
        pool_max=20
    )
        success = await schema_manager.create_connector("postgresql", "pg_source", pg_config)
        if success:
            # Get tables
            tables = await schema_manager.get_tables("pg_source", schema="public")
            # Initialize result
            if not tables:
                return {}
            # Get schema for third table
            schema = await schema_manager.get_schema("pg_source", tables[3], schema="public")
            
            if not any(schema.values()):
                return {}
            result = {
                    "sink_schema": {
                        "fields": []
                    },
                    "transform_sql": None
                }
            fields = schema["fields"]
            result["sink_schema"]["fields"] = [
                {"name": col_name, "type": col_type, "required": col_name in (primary_keys or [])}
                for col_name, col_type in fields.items()
            ]
        

    def create_job(self, name: str, config: JobConfig) -> JobResponse:
        config_dict = config.dict(by_alias=True)
        print(config_dict)
        job_config = {"name": name, "config": config_dict}
        
        # Send the request to the SeaTunnel API
        response = self.client.create_job(job_config)
        
        # Return a JobResponse object
        return JobResponse(
            job_id=response.get("jobId", "unknown"),
            status=response.get("status", "CREATED"),
            name=name,
            created_at=response.get("createdAt")
        )

    def get_job(self, job_id: str) -> Dict[str, Any]:
        return self.client.get_job(job_id)

    def get_job_status(self, job_id: str) -> str:
        """Get the status of a job"""
        response = self.client.get_job(job_id)
        return response.get("status", "UNKNOWN")
    
    def stop_job(self, job_id: str, save_point: bool = False) -> None:
        """Stop a running job"""
        stop_config = {
            "jobId": job_id,
            "isStopWithSavePoint": save_point
        }
        self.client._request("POST", "/stop-job", data=stop_config)