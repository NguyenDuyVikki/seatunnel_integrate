from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json

@dataclass
class TableConfig:
    name: str
    schema: Optional[Dict] = None
    filters: Optional[Dict] = None

@dataclass
class AuthConfig:
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: Optional[Dict] = None

@dataclass
class SourceConfig:
    source_type: str
    auth: Optional[AuthConfig] = None
    tables: List[TableConfig] = None
    config: Optional[Dict] = None

    def __post_init__(self):
        if self.tables is None:
            self.tables = []

@dataclass
class SinkConfig:
    sink_type: str
    auth: Optional[AuthConfig] = None
    config: Optional[Dict] = None

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
                            if field_type == List[TableConfig]:
                                kwargs[field] = [convert(item, TableConfig) for item in value]
                            elif field_type in (AuthConfig, SourceConfig, SinkConfig):
                                kwargs[field] = convert(value, field_type)
                            else:
                                kwargs[field] = value
                    return cls(**kwargs)
            return data
        return convert(data, cls)