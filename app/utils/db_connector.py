from typing import Dict, List, Any, Optional, Union
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
import asyncpg
import aiomysql
import oracledb
from tenacity import retry, stop_after_attempt, wait_exponential
import re
# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DBConfig:
    """Database configuration class"""
    host: str
    port: int
    username: str
    password: str
    database: Optional[str] = None
    service_name: Optional[str] = None
    pool_min: int = 1
    pool_max: int = 10

def retry_on_failure(func):
    """Decorator for retrying database operations"""
    @wraps(func)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

class DBConnector(ABC):
    """Abstract base class for database connectors"""
    
    def __init__(self, config: DBConfig):
        self.config = config
        self.pool = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection pool to the database"""
        pass

    @abstractmethod
    async def get_tables(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[str]:
        """Get list of tables in the database/schema"""
        pass

    @abstractmethod
    async def get_columns(self, table: str, database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, str]:
        """Get column names and types for a specific table"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection pool"""
        pass

class PostgreSQLConnector(DBConnector):
    
    async def connect(self) -> bool:
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.pool_min,
                max_size=self.config.pool_max
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            return False

    @retry_on_failure
    async def get_tables(self, database: Optional[str] = None, schema: str = "public") -> List[str]:
        if not self.pool:
            if not await self.connect():
                return []
        
        async with self.pool.acquire() as conn:
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = $1
            """
            tables = [row['table_name'] for row in await conn.fetch(query, schema)]
            return tables

    @retry_on_failure
    async def get_columns(self, table: str, database: Optional[str] = None, schema: str = "public") -> Dict[str, str]:
        if not self.pool:
            if not await self.connect():
                return {}
        
        async with self.pool.acquire() as conn:
            query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            """
            columns = {
                row['column_name']: self._map_type_to_seatunnel(row['data_type']) 
                for row in await conn.fetch(query, schema, table)
            }
            return columns

    def _map_type_to_seatunnel(self, pg_type: str) -> str:
        """Map database types to SeaTunnel compatible types"""
        type_mapping = {
            "integer": "int",
            "bigint": "long",
            "smallint": "short",
            "character varying": "string",
            "varchar": "string",
            "text": "string",
            "double precision": "double",
            "numeric": "decimal",
            "real": "float",
            "boolean": "boolean",
            "date": "date",
            "timestamp": "timestamp",
            "time": "time"
        }
        return type_mapping.get(pg_type.lower(), "string")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

class MySQLConnector(DBConnector):
    """MySQL async connector implementation"""
    
    async def connect(self) -> bool:
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                minsize=self.config.pool_min,
                maxsize=self.config.pool_max
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            return False

    @retry_on_failure
    async def get_tables(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[str]:
        if not self.pool:
            if not await self.connect():
                return []
        
        db = database or self.config.database
        if not db:
            logger.error("Database name is required for MySQL")
            return []
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                tables = [row[0] for row in await cursor.fetchall()]
                return tables

    @retry_on_failure
    async def get_columns(self, table: str, database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, str]:
        if not self.pool:
            if not await self.connect():
                return {}
        
        db = database or self.config.database
        if not db:
            logger.error("Database name is required for MySQL")
            return {}
            
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"DESCRIBE {table}")
                columns = {
                    row[0]: self._map_type_to_seatunnel(row[1])
                    for row in await cursor.fetchall()
                }
                return columns

    def _map_type_to_seatunnel(self, mysql_type: str) -> str:
        """Map MySQL types to SeaTunnel compatible types"""
        mysql_type = mysql_type.lower()
        type_mapping = {
            r"\bint\b": "int",
            r"\bbigint\b": "long",
            r"\b(varchar|text|char)\b": "string",
            r"\b(double|float)\b": "double",
            r"\bdecimal\b": "decimal",
            r"\bdate\b": "date",
            r"\b(datetime|timestamp)\b": "timestamp",
            r"\bbool(ean)?\b": "boolean",
            r"\btime\b": "time"
        }
        for pattern, seatunnel_type in type_mapping.items():
            if re.search(pattern, mysql_type):
                return seatunnel_type
        return "string"

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

class OracleConnector(DBConnector):
    """Oracle async connector implementation"""
    
    async def connect(self) -> bool:
        try:
            oracledb.init_oracle_client()
            self.pool = oracledb.create_pool(
                user=self.config.username,
                password=self.config.password,
                dsn=f"{self.config.host}:{self.config.port}/{self.config.service_name}",
                min=self.config.pool_min,
                max=self.config.pool_max,
                increment=1
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Oracle: {str(e)}")
            return False

    @retry_on_failure
    async def get_tables(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[str]:
        if not self.pool:
            if not await self.connect():
                return []
        
        owner = schema or self.config.username.upper()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT table_name FROM all_tables WHERE owner = :owner",
                    {"owner": owner}
                )
                tables = [row[0] for row in await cursor.fetchall()]
                return tables

    @retry_on_failure
    async def get_columns(self, table: str, database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, str]:
        if not self.pool:
            if not await self.connect():
                return {}
        
        owner = schema or self.config.username.upper()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT column_name, data_type 
                    FROM all_tab_columns 
                    WHERE owner = :owner AND table_name = :table
                    ORDER BY column_id
                    """,
                    {"owner": owner, "table": table.upper()}
                )
                columns = {
                    row[0]: self._map_type_to_seatunnel(row[1])
                    for row in await cursor.fetchall()
                }
                return columns

    def _map_type_to_seatunnel(self, oracle_type: str) -> str:
        """Map Oracle types to SeaTunnel compatible types"""
        oracle_type = oracle_type.upper()
        type_mapping = {
            "NUMBER|INTEGER": "int",
            "FLOAT": "float",
            "CHAR|VARCHAR|CLOB": "string",
            "DATE": "date",
            "TIMESTAMP": "timestamp",
            "BINARY_FLOAT|BINARY_DOUBLE": "double",
            "BLOB": "bytes",
            "BOOLEAN": "boolean"
        }
        for pattern, seatunnel_type in type_mapping.items():
            if any(t in oracle_type for t in pattern.split("|")):
                return seatunnel_type
        return "string"

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            self.pool = None

class ConnectorFactory:
    """Factory for creating database connectors dynamically"""
    
    CONNECTOR_TYPES = {
        "postgresql": PostgreSQLConnector,
        "mysql": MySQLConnector,
        "oracle": OracleConnector
    }
    
    @classmethod
    def create_connector(cls, db_type: str, config: DBConfig) -> Optional[DBConnector]:
        connector_class = cls.CONNECTOR_TYPES.get(db_type.lower())
        if not connector_class:
            logger.error(f"Unsupported database type: {db_type}")
            return None
        return connector_class(config)

class SchemaManager:
    """Manager for handling multiple database connectors and schema operations"""
    
    def __init__(self):
        self.connectors: Dict[str, DBConnector] = {}
        
    async def add_connector(self, name: str, connector: DBConnector) -> None:
        """Add a database connector with a unique name"""
        self.connectors[name] = connector
        
    async def create_connector(
        self, 
        db_type: str, 
        name: str, 
        config: DBConfig
    ) -> bool:
        """Create and add a connector for a specific database type"""
        connector = ConnectorFactory.create_connector(db_type, config)
        if not connector:
            return False
            
        if await connector.connect():
            await self.add_connector(name, connector)
            return True
        return False

    async def get_tables(self, connector_name: str, database: Optional[str] = None, schema: Optional[str] = None) -> List[str]:
        """Get list of tables from a specific database connector"""
        connector = self.connectors.get(connector_name)
        if not connector:
            logger.error(f"Connector '{connector_name}' not found")
            return []
        return await connector.get_tables(database, schema)

    async def get_schema(
        self, 
        connector_name: str, 
        table: str, 
        database: Optional[str] = None, 
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get schema for a specific table formatted for SeaTunnel"""
        connector = self.connectors.get(connector_name)
        if not connector:
            logger.error(f"Connector '{connector_name}' not found")
            return {}
            
        columns = await connector.get_columns(table, database, schema)
        return {"fields": columns} if columns else {}

    async def get_schema_for_multiple_tables(
        self, 
        connector_name: str, 
        tables: List[str], 
        database: Optional[str] = None, 
        schema: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get schema for multiple tables at once"""
        tasks = [
            self.get_schema(connector_name, table, database, schema)
            for table in tables
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            table: result if isinstance(result, dict) else {}
            for table, result in zip(tables, results)
        }

    async def close_connector(self, connector_name: str) -> None:
        """Close a specific database connector"""
        connector = self.connectors.get(connector_name)
        if connector:
            await connector.close()
            del self.connectors[connector_name]

    async def close_all_connectors(self) -> None:
        """Close all database connectors"""
        tasks = [self.close_connector(name) for name in list(self.connectors.keys())]
        await asyncio.gather(*tasks)

async def main():
    """Example usage"""
    schema_manager = SchemaManager()
    
    # PostgreSQL configuration
    pg_config = DBConfig(
        host="localhost",
        port=5432,
        username="db_cluster_viewer",
        password="qfxu4dUDHZlJ",
        database="account",
        pool_min=2,
        pool_max=20
    )
    
    # Create PostgreSQL connector
    success = await schema_manager.create_connector("postgresql", "pg_source", pg_config)
    
    if success:
        # Get tables
        tables = await schema_manager.get_tables("pg_source", schema="public")
        print(f"Tables: {tables}")
        
        # Get schema for first table
        if tables:
            schema = await schema_manager.get_schema("pg_source", tables[3], schema="public")
            print(json.dumps(schema, indent=2))
    
    # Clean up
    await schema_manager.close_all_connectors()

if __name__ == "__main__":
    asyncio.run(main())