
import requests
from typing import Optional, Dict, Any
from app.config.setting import settings  # import your SETTINGS instance
import json

class SeaTunnelClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        # Use provided base_url or fallback to settings.API_URL
        raw_url = base_url or settings.API_URL
        self.base_url = raw_url.rstrip('/').split('/submit-job')[0]
        
        self.api_key = api_key or settings.API_KEY
        
        self.timeout = timeout or settings.TIMEOUT
        
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Build URL: e.g. http://host:port + /submit-job
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            job_config = json_data.get("config")
            create_job = {
                    "params": {
                        "jobId": job_config.get("jobId"),
                        "jobName": job_config.get("jobName"),
                    },
                    "env": job_config['config'].get("env"),
                    "source": job_config['config'].get("source"),
                    "transform": job_config['config'].get("transform", []),
                    "sink": job_config['config'].get("sink"),
                }

            resp = self.session.request(
                method=method,
                url=url,
                json=create_job,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            # include status and body (if any) in the exception
            status = getattr(e.response, "status_code", None)
            body = getattr(e.response, "text", None)
            raise Exception(
                f"HTTP {method} {url} failed"
                f"{f' with status {status}' if status else ''}: {e}"
                f"{f' — response body: {body}' if body else ''}"
            ) from e
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        # GET /jobs/{job_id}
        return self._request("GET", f"jobs/{job_id}")
    
    def create_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        # POST /submit-job
        return self._request("POST", "submit-job", json_data=job_config)
