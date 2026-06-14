import os

class Settings:
    PROJECT_NAME: str = "Restaurant Analytics SaaS"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://analytics_user:analytics_password@localhost/restaurant_analytics"
    )

settings = Settings()
