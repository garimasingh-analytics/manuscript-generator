from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "manuscript_writer"

    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60 * 24 * 7

    litellm_model: str = "claude-sonnet-4-5"
    litellm_api_key: str = ""

    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

