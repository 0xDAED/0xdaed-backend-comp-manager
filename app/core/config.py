from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = False

    postgres_dsn: str
    redis_dsn: str

    heartbeat_ttl_seconds: int = 60
    max_commands_per_heartbeat: int = 10

    agent_token_secret: str = "change-me"

settings = Settings()
