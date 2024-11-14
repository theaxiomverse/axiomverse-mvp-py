from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any
import yaml
import os
from functools import lru_cache

class VectorQuantumSettings(BaseSettings):
    encoding: str = "standard"
    qubits: int = 8
    error_correction: bool = True

class VectorSettings(BaseSettings):
    dimensions: int = 8
    precision: int = 6
    batch_size: int = 100
    storage_path: str = "data/vectors"
    quantum: VectorQuantumSettings

class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    backlog: int = 2048
    debug: bool = False


class SecuritySettings(BaseSettings):
    ssl_enabled: bool = True
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry: int = 3600


class ConsensusSettings(BaseSettings):
    threshold: float = 0.67
    min_nodes: int = 3
    timeout: int = 30
    batch_size: int = 100


class PerformanceSettings(BaseSettings):
    max_connections: int = 10000
    keep_alive: int = 5
    cache_ttl: int = 300
    max_cache_size: int = 1000
    connection_timeout: int = 30


class MonitoringSettings(BaseSettings):
    prometheus_enabled: bool = True
    prometheus_port: int = 8001
    metrics_path: str = "/metrics"
    collect_default_metrics: bool = True


class LoggingSettings(BaseSettings):
    level: str = "DEBUG"
    json_format: bool = True
    file_path: str = "logs/app.log"
    max_size: int = 10485760
    backup_count: int = 5


class NodeSettings(BaseSettings):
    heartbeat_interval: int = 10
    cleanup_interval: int = 60
    inactive_threshold: int = 300


class VaultSettings(BaseSettings):
    addr: str = "http://vault:8200"
    mount_point: str = "axiomverse"
    token_path: str = "/run/secrets/vault_token"


class NatsSettings(BaseSettings):
    url: str = "nats://nats:4222"
    auth_token_path: str = "/run/secrets/nats_token"
    cluster_name: str = "axiomverse"
    client_id: str = "axiomverse-api"


class Settings(BaseSettings):
    # API Configuration
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Component Settings
    vector: VectorSettings
    server: ServerSettings
    security: SecuritySettings
    consensus: ConsensusSettings
    performance: PerformanceSettings
    monitoring: MonitoringSettings
    logging: LoggingSettings
    nodes: NodeSettings
    vault: VaultSettings
    nats: NatsSettings

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_vault_token(self) -> str:
        """Read Vault token from file."""
        try:
            with open(self.vault.token_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"Failed to read Vault token: {e}")

    def get_nats_token(self) -> str:
        """Read NATS token from file."""
        try:
            with open(self.nats.auth_token_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"Failed to read NATS token: {e}")


@lru_cache()
def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = os.getenv("CONFIG_FILE", "config.yaml")
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config file: {e}")


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance with loaded configuration."""
    config = load_config()

    # Ensure JWT secret is set
    if 'JWT_SECRET' not in os.environ and ('security' not in config or 'jwt_secret' not in config['security']):
        raise ValueError("JWT_SECRET must be set in environment or config file")

    return Settings(**config)


settings = get_settings()