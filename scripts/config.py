from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    openai_model: str = "gpt-5-nano"
    openai_api_key: SecretStr

    colqwen_model: str = 'vidore/colqwen2-v1.0-hf'
    sparse_embedding_model: str = 'prithvida/Splade_PP_en_v1'

    qwen3vl_model : str = "Qwen/Qwen3-VL-2B-Instruct"

    hf_token: SecretStr

    jina_url: str 
    jina_api_key: SecretStr

    qdrant_cluster_endpoint: str
    qdrant_collection_name: str 
    qdrant_api_key: SecretStr

    supabase_url: str
    supabase_key: SecretStr
    supabase_bucket_name : str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()



'''
from scripts.config import settings

model = settings.openai_model
# Use .get_secret_value() specifically for SecretStr variables
api_key = settings.openai_api_key.get_secret_value() 
'''