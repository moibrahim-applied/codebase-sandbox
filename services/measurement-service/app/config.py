from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    redis_namespace: str = "mt:measurement"
    audit_retention_days: int = 2555  # 7 years — CFR 21 Part 11 minimum.
    gwp_profile: str = "default"
    max_payload_bytes: int = 65_536

    class Config:
        env_prefix = "MT_MEAS_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
