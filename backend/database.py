import pyodbc
import os

# Direct connection string - no dotenv needed
SQL_CONNECTION_STRING = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:lahari-finance-server-2025.database.windows.net,1433;Database=FinanceDB;Uid=adminuser;Pwd=MyStrongPassword123!;Connection Timeout=30;"

class DatabaseManager:
    
    def __init__(self):
        self.connection_string = SQL_CONNECTION_STRING
    
    def get_connection(self):
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    def create_tables(self):
        conn = self.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            print("Creating all tables...")
            
            # 1. Users table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE [Users] (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(255) UNIQUE NOT NULL,
                email NVARCHAR(255) UNIQUE NOT NULL,
                password_hash NVARCHAR(255) NOT NULL,
                first_name NVARCHAR(100),
                last_name NVARCHAR(100),
                risk_tolerance NVARCHAR(20) DEFAULT 'moderate',
                investment_goals NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                is_active BIT DEFAULT 1
            )
            """)
            
            # 2. Stocks table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Stocks' AND xtype='U')
            CREATE TABLE Stocks (
                id INT IDENTITY(1,1) PRIMARY KEY,
                symbol NVARCHAR(10) UNIQUE NOT NULL,
                company_name NVARCHAR(255) NOT NULL,
                sector NVARCHAR(100),
                industry NVARCHAR(100),
                current_price DECIMAL(10,2),
                price_change DECIMAL(10,2),
                price_change_percent DECIMAL(5,2),
                volume BIGINT,
                market_cap BIGINT,
                pe_ratio DECIMAL(8,2),
                dividend_yield DECIMAL(5,2),
                high_52_week DECIMAL(10,2),
                low_52_week DECIMAL(10,2),
                beta DECIMAL(5,2),
                description NVARCHAR(MAX),
                last_updated DATETIME2 DEFAULT GETDATE()
            )
            """)
            
            # 3. Portfolio table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Portfolio' AND xtype='U')
            CREATE TABLE Portfolio (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                stock_symbol NVARCHAR(10) NOT NULL,
                quantity INT NOT NULL,
                purchase_price DECIMAL(10,2) NOT NULL,
                purchase_date DATETIME2 DEFAULT GETDATE(),
                current_value DECIMAL(12,2),
                gain_loss DECIMAL(10,2),
                gain_loss_percent DECIMAL(5,2),
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol)
            )
            """)
            
            # 4. Transactions table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Transactions' AND xtype='U')
            CREATE TABLE Transactions (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                stock_symbol NVARCHAR(10) NOT NULL,
                transaction_type NVARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(12,2) NOT NULL,
                fees DECIMAL(8,2) DEFAULT 0,
                transaction_date DATETIME2 DEFAULT GETDATE(),
                notes NVARCHAR(MAX),
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol)
            )
            """)
            
            # 5. Watchlist table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Watchlist' AND xtype='U')
            CREATE TABLE Watchlist (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                stock_symbol NVARCHAR(10) NOT NULL,
                added_date DATETIME2 DEFAULT GETDATE(),
                target_price DECIMAL(10,2),
                notes NVARCHAR(MAX),
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol),
                UNIQUE(user_id, stock_symbol)
            )
            """)
            
            # 6. Historical_Prices table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Historical_Prices' AND xtype='U')
            CREATE TABLE Historical_Prices (
                id INT IDENTITY(1,1) PRIMARY KEY,
                stock_symbol NVARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                volume BIGINT,
                adjusted_close DECIMAL(10,2),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol),
                UNIQUE(stock_symbol, date)
            )
            """)
            
            # 7. News table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='News' AND xtype='U')
            CREATE TABLE News (
                id INT IDENTITY(1,1) PRIMARY KEY,
                title NVARCHAR(255) NOT NULL,
                content NVARCHAR(MAX),
                source NVARCHAR(100),
                author NVARCHAR(100),
                url NVARCHAR(500),
                published_date DATETIME2,
                stock_symbol NVARCHAR(10),
                sentiment_score DECIMAL(3,2),
                category NVARCHAR(50),
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol)
            )
            """)
            
            # 8. AI_Analysis table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AI_Analysis' AND xtype='U')
            CREATE TABLE AI_Analysis (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                stock_symbol NVARCHAR(10),
                analysis_type NVARCHAR(50) NOT NULL,
                analysis_result NVARCHAR(MAX) NOT NULL,
                confidence_score DECIMAL(3,2),
                recommendations NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol)
            )
            """)
            
            # 9. Alerts table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Alerts' AND xtype='U')
            CREATE TABLE Alerts (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                stock_symbol NVARCHAR(10) NOT NULL,
                alert_type NVARCHAR(20) NOT NULL CHECK (alert_type IN ('PRICE_ABOVE', 'PRICE_BELOW', 'VOLUME_SPIKE', 'NEWS')),
                trigger_value DECIMAL(10,2),
                message NVARCHAR(MAX),
                is_active BIT DEFAULT 1,
                is_triggered BIT DEFAULT 0,
                created_at DATETIME2 DEFAULT GETDATE(),
                triggered_at DATETIME2,
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                FOREIGN KEY (stock_symbol) REFERENCES Stocks(symbol)
            )
            """)
            
            # 10. User_Preferences table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='User_Preferences' AND xtype='U')
            CREATE TABLE User_Preferences (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                preference_key NVARCHAR(100) NOT NULL,
                preference_value NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES [Users](id),
                UNIQUE(user_id, preference_key)
            )
            """)
            
            # 11. Market_Sectors table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Market_Sectors' AND xtype='U')
            CREATE TABLE Market_Sectors (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sector_name NVARCHAR(100) UNIQUE NOT NULL,
                description NVARCHAR(MAX),
                performance_1d DECIMAL(5,2),
                performance_1w DECIMAL(5,2),
                performance_1m DECIMAL(5,2),
                performance_ytd DECIMAL(5,2),
                last_updated DATETIME2 DEFAULT GETDATE()
            )
            """)
            
            # 12. Economic_Indicators table
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Economic_Indicators' AND xtype='U')
            CREATE TABLE Economic_Indicators (
                id INT IDENTITY(1,1) PRIMARY KEY,
                indicator_name NVARCHAR(100) NOT NULL,
                indicator_value DECIMAL(10,4),
                previous_value DECIMAL(10,4),
                change_percent DECIMAL(5,2),
                date_reported DATE,
                frequency NVARCHAR(20),
                source NVARCHAR(100),
                created_at DATETIME2 DEFAULT GETDATE()
            )
            """)
            
            # 13. Chat_History table (for AI conversations)
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Chat_History' AND xtype='U')
            CREATE TABLE Chat_History (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                message NVARCHAR(MAX) NOT NULL,
                response NVARCHAR(MAX) NOT NULL,
                message_type NVARCHAR(50),
                session_id NVARCHAR(100),
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES [Users](id)
            )
            """)
            
            conn.commit()
            print("All 13 tables created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
            return False
        
        finally:
            conn.close()
    
    def setup_database(self):
        print("Setting up complete FinanceAI database...")
        if self.create_tables():
            print("Database setup completed successfully")
            return True
        else:
            print("Database setup failed")
            return False

def run_database_setup():
    db_manager = DatabaseManager()
    return db_manager.setup_database()

if __name__ == "__main__":
    print("FinanceAI - Complete Database Setup")
    print("=" * 40)
    
    success = run_database_setup()
    
    if success:
        print("Database setup completed successfully")
    else:
        print("Database setup failed")