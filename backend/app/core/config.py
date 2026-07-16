from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "xephon_admin"
    postgres_user: str = "xephon_admin"
    postgres_password: str = "change-me"

    cors_origins: str = "http://localhost:5177"

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "xephon"
    keycloak_client_id: str = "xephon-admin"

    # Service account used to call Keycloak Admin API
    keycloak_admin_client_id: str = "xephon-admin-sa"
    keycloak_admin_client_secret: str = "change-me-admin-sa"

    # Role required to access this service
    admin_role: str = "xephon:admin"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_admin_base(self) -> str:
        return f"{self.keycloak_url}/admin/realms/{self.keycloak_realm}"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/token"


settings = Settings()
