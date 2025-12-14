from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MySQL Configuration
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "stockmarket_user"
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str = "stockmarket_db"
    
    # OpenAI Configuration (Azure GPT-4o for analysis)
    AZURE_OPENAI_API_KEY: str = "cefee778f5a84607b84de9732eb75aa6"
    AZURE_OPENAI_ENDPOINT: str = "https://unstructured-docinfo-extraction.openai.azure.com"
    AZURE_OPENAI_DEPLOYMENT: str = "KYC-DocInfo-GPT4o"
    AZURE_OPENAI_API_VERSION: str = "2023-07-01-preview"
    
    # Note: Using local sentence-transformers for embeddings (no Azure deployment needed)
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours (was 15 mins - too short!)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    
    # Application Configuration
    APP_NAME: str = "AI Market Analysis Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Data Storage
    DATA_DIR: str = "/app/data"
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # ChromaDB Dynamic Temporal Retrieval Configuration
    TEMPORAL_DECAY_LAMBDA: float = 0.05  # Decay rate for temporal scoring
    TEMPORAL_WEIGHT: float = 0.6  # Weight for recency in combined score  
    QUALITY_WEIGHT: float = 0.4  # Weight for quality in combined score
    MAX_PER_WEEK: int = 2  # Max analyses per week for temporal diversity
    TARGET_ANALYSES: int = 5  # Number of historical analyses to return
    DAYS_BACK: int = 45  # How far back to look for historical analyses
    
    # Stock API Configuration
    STOCK_API_BASE_URL: str = "https://indian-stock-exchange-api.p.rapidapi.com"
    
    # Scraper Configuration
    SCRAPER_DELAY_SECONDS: int = 2
    MAX_ARTICLES_PER_SOURCE: int = 50
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072
    
    # Sentiment Configuration
    SENTIMENT_MODEL: str = "gpt-4o-mini"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    ENABLE_DETAILED_LOGS: bool = True  # Enable detailed parameter logging
    LOG_FORMAT: str = "structured"  # structured or simple
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True  # Set to False to disable rate limiting
    
    # Smart API Orchestrator Feature Flag
    USE_SMART_ORCHESTRATOR: bool = False  # Default: OFF (safe deployment)
    SMART_ORCHESTRATOR_TIMEOUT: float = 5.0  # Parallel execution timeout (seconds)
    
    @property
    def database_url(self) -> str:
        """Construct MySQL database URL."""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        # Try multiple .env file locations
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
