import os

class Settings:
    PROJECT_NAME: str = "GastroSense Analytics"
    API_V1_STR: str = "/api/v1"
    
    # Use SQLite by default for easy portfolio running without a DB server
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./analytics.db"
    )

settings = Settings()
