from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COPILOT_", env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    bedrock_model_id: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    analyzer_mode: str = "mock"
    queue_url: str = ""
    notification_topic_arn: str = ""
    log_level: str = "INFO"
    poll_wait_seconds: int = 10
    max_log_lines: int = 40


@lru_cache
def get_settings() -> Settings:
    return Settings()
