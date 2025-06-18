import os

class Config:
    # Database settings
    SQL_CONNECTION_STRING = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:lahari-finance-server-2025.database.windows.net,1433;Database=FinanceDB;Uid=adminuser;Pwd=MyStrongPassword123!;Connection Timeout=30;"
    
    # Flask settings
    SECRET_KEY = 'your-secret-key-change-this-later'
    DEBUG = True
    
    # API settings
    STOCK_API_DELAY = 0.1  # Delay between API calls
    MAX_STOCKS_PER_REQUEST = 100
    
    # Update intervals
    PRICE_UPDATE_INTERVAL = 300  # 5 minutes
    NEWS_UPDATE_INTERVAL = 1800  # 30 minutes
    
    # Default user for testing
    DEFAULT_USER_ID = 1

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Use development config by default
config = DevelopmentConfig()