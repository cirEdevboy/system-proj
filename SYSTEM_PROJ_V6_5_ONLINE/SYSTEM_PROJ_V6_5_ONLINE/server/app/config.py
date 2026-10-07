from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Project Center"
    env: str = "development"
    domain: str = "localhost"

    database_url: str = "sqlite:///./system_proj_v6_dev.db"

    jwt_secret: str = "DEV-CHANGE-ME"
    access_token_minutes: int = 20
    refresh_token_days: int = 30
    cors_origins: str = "http://localhost:8000"

    storage_mode: str = "local"
    s3_endpoint: str = ""
    s3_bucket: str = "systemproj"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "auto"
    local_storage_path: str = "./data/files"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "systemproj@empresa.com"
    smtp_starttls: bool = True
    web_base_url: str = ""

    # --------------------------------------------------------
    # MASTER ADMIN
    # --------------------------------------------------------
    # No servidor online os dados pessoais/senha do MASTER_ADMIN
    # não ficam gravados no repositório. O Render solicita estes
    # valores como variáveis secretas durante a implantação.
    master_admin_enabled: bool = False
    master_admin_username: str = ""
    master_admin_email: str = ""
    master_admin_badge: str = ""
    master_admin_full_name: str = ""
    master_admin_password: str = ""

    # --------------------------------------------------------
    # HEARTBEAT / KEEPALIVE
    # --------------------------------------------------------
    # Mantido como recurso configurável de teste/monitoramento.
    # No plano pago 24h ele deve ficar DESATIVADO.
    keepalive_enabled: bool = False
    keepalive_interval_minutes: int = 14
    keepalive_urls: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        """
        O Render fornece connectionString como postgresql://...
        SQLAlchemy sem psycopg2 tentaria usar o driver antigo.
        Normalizamos para psycopg 3, que já faz parte do projeto.
        """
        value = str(value or "").strip()

        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://"):]

        if (
            value.startswith("postgresql://")
            and not value.startswith("postgresql+psycopg://")
        ):
            return (
                "postgresql+psycopg://"
                + value[len("postgresql://"):]
            )

        return value

    @property
    def cors_list(self):
        return [
            x.strip()
            for x in self.cors_origins.split(",")
            if x.strip()
        ]

    @property
    def public_base_url(self) -> str:
        explicit = str(self.web_base_url or "").strip().rstrip("/")

        if explicit:
            return explicit

        render_host = os.getenv(
            "RENDER_EXTERNAL_HOSTNAME",
            "",
        ).strip()

        if render_host:
            return f"https://{render_host}"

        return "http://localhost:8000"

    @property
    def keepalive_url_list(self) -> list[str]:
        """
        Array efetivo de endpoints que o heartbeat consulta.

        KEEPALIVE_URLS aceita:
        https://site-a/health,https://site-b/health

        Em Render, quando nenhum URL é informado, o próprio endereço
        público do serviço entra automaticamente na lista.
        """
        urls = [
            x.strip().rstrip("/")
            for x in str(self.keepalive_urls or "").split(",")
            if x.strip()
        ]

        render_host = os.getenv(
            "RENDER_EXTERNAL_HOSTNAME",
            "",
        ).strip()

        if render_host:
            self_url = (
                f"https://{render_host}/api/v1/health"
            )

            if self_url not in urls:
                urls.append(self_url)

        return urls


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
