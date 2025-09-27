from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # OpenAI API Settings
    OPENAI_API_KEY: str | None = None  # Allow key to be optional to enable server startup
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MODEL_CHEAT_CHECK: str = "qwen3-235b-a22b"

    # Optional Gemini/AI Provider Settings (scaffold; safe defaults)
    AI_PROVIDER: str = "openai"  # options: openai|gemini|auto
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_BASE_URL: str | None = None
    AI_PROVIDER_FALLBACK: str = "openai"
    BLOCK_GEMINI_IN_MAINLAND: bool = True

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600

    # Database URL
    DATABASE_URL: str = "sqlite:///./veloera.db"

    # Feature Toggles
    REDEMPTION_ENABLED: bool = False
    INHERITANCE_ENABLED: bool = True
    BANNED_REFRESH_BLOCK: bool = True

    # Authentication Settings (Simple Username/Password)
    AUTH_USERS: str | None = None  # Format: username1:password1,username2:password2

    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    UVICORN_RELOAD: bool = True

    # Point to the .env file in the 'backend' directory relative to the project root
    model_config = SettingsConfigDict(env_file="backend/.env")

# Create a single instance of the settings
settings = Settings()