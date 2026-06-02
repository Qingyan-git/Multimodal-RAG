from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    openai_model: str = "gpt-40-mini"
    openai_api_key: SecretStr

    hf_token: SecretStr

    jina_api_key: SecretStr

    qdrant_url: str 
    qdrant_api_key: SecretStr

    supabase_url: str
    supabase_key: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()