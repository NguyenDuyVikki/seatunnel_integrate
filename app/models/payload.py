from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import json



@dataclass
class AuthConfig:
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: Optional[Dict] = None

@dataclass
class SourceConfig:
    source_type: str
    auth: Optional[AuthConfig] = None
    config: Optional[Dict] = None


            
# @dataclass
# class KafkaSourceConfig:
#     topic: str
#     bootstrap_servers: str
#     partition: int = 1
#     format: str = "json"
#     schema_registry_url: Optional[str] = None
#     key_deserializer: Optional[str] = None
#     value_deserializer: Optional[str] = None

@dataclass
class SinkConfig:
    sink_type: str
    auth: Optional[AuthConfig] = None
    config: Optional[Dict] = None
    
    def __post_init__(self):
        if self.auth is None:
            self.auth = []

@dataclass
class SeaTunnelRequest:
    source: SourceConfig
    sink: SinkConfig

    def to_json(self) -> str:
        def filter_none(d):
            if isinstance(d, dict):
                return {k: filter_none(v) for k, v in d.items() if v is not None}
            elif isinstance(d, list):
                return [filter_none(item) for item in d if item is not None]
            return d
        return json.dumps(filter_none(asdict(self)))

    @classmethod
    def from_dict(cls, data: Dict) -> 'SeaTunnelRequest':
        def convert(data, cls):
            if isinstance(data, dict):
                if hasattr(cls, '__dataclass_fields__'):
                    kwargs = {}
                    for field in cls.__dataclass_fields__:
                        value = data.get(field)
                        field_type = cls.__dataclass_fields__[field].type
                        if value is not None:
                            if field_type == List[str]:
                                kwargs[field] = [convert(item, str) for item in value]
                            elif field_type in (AuthConfig, SourceConfig, SinkConfig):
                                kwargs[field] = convert(value, field_type)
                            else:
                                kwargs[field] = value
                    return cls(**kwargs)
            return data
        return convert(data, cls)
    
    
def map_source_item(item: Dict[str, Any]) -> SourceConfig:
    source_config = SourceConfig(**item)  # Create SourceConfig from the dictionary
    print(f"SourceConfig: {source_config}")
    return source_config