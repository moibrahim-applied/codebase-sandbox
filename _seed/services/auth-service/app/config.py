from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT issuer + audience claims.
    jwt_issuer: str = "https://auth.freeweigh.mt.internal"
    jwt_audience: str = "freeweigh-console"
    jwt_ttl_seconds: int = 3600
    jwt_algorithm: str = "HS256"

    # Dev-only secret. Real deployments load from Vault.
    jwt_secret: str = "change-me-in-prod"

    # LDAP — stubbed in the sandbox. The real config points at the MT
    # corporate Active Directory.
    ldap_url: str = "ldaps://ldap.mt.internal:636"
    ldap_base_dn: str = "OU=FreeWeigh,DC=mt,DC=internal"
    ldap_bind_user: str = "svc-auth"

    class Config:
        env_prefix = "MT_AUTH_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
