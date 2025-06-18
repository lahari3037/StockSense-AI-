import requests
import pandas as pd
import yfinance as yf
import pyodbc
import os
from dotenv import load_dotenv
import time
from datetime import datetime
from io import StringIO

SQL_CONNECTION_STRING = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:lahari-finance-server-2025.database.windows.net,1433;Database=FinanceDB;Uid=adminuser;Pwd=MyStrongPassword123!;Connection Timeout=30;"

class StockDataLoader:
    
    def __init__(self):
        self.connection_string = SQL_CONNECTION_STRING
    
    def get_connection(self):
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    def download_sp500_companies(self):
        print("Downloading S&P 500 companies from Wikipedia...")
        
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            
            tables = pd.read_html(StringIO(response.text))
            sp500_table = tables[0]
            
            companies = []
            for index, row in sp500_table.iterrows():
                companies.append({
                    'symbol': str(row['Symbol']).strip(),
                    'company_name': str(row['Security']).strip(),
                    'sector': str(row['GICS Sector']).strip(),
                    'industry': str(row['GICS Sub-Industry']).strip()
                })
            
            print(f"Downloaded {len(companies)} S&P 500 companies")
            return companies
            
        except Exception as e:
            print(f"Failed to download S&P 500 data: {e}")
            return []
    
    def get_stock_prices_bulk(self, symbols):
        print(f"Getting current prices for {len(symbols)} stocks...")
        
        price_data = []
        
        for symbol in symbols[:50]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    
                    price_change = current_price - previous_close
                    price_change_percent = (price_change / previous_close) * 100 if previous_close != 0 else 0
                    
                    info = ticker.info
                    
                    price_data.append({
                        'symbol': symbol,
                        'current_price': round(current_price, 2),
                        'price_change': round(price_change, 2),
                        'price_change_percent': round(price_change_percent, 2),
                        'volume': info.get('volume', 0),
                        'market_cap': info.get('marketCap', 0)
                    })
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Failed to get price for {symbol}: {e}")
                continue
        
        print(f"Retrieved prices for {len(price_data)} stocks")
        return price_data
    
    def load_companies_to_database(self, companies_list):
        if not companies_list:
            print("No companies to load")
            return False
        
        conn = self.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            print(f"Loading {len(companies_list)} companies into database...")
            
            for company in companies_list:
                cursor.execute("""
                INSERT INTO Stocks (symbol, company_name, sector, industry, current_price, 
                                  price_change, price_change_percent, volume, market_cap, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                company['symbol'],
                company['company_name'],
                company.get('sector', 'Unknown'),
                company.get('industry', 'Unknown'),
                company.get('current_price', 0),
                company.get('price_change', 0),
                company.get('price_change_percent', 0),
                company.get('volume', 0),
                company.get('market_cap', 0),
                datetime.now())
            
            conn.commit()
            print(f"Successfully loaded {len(companies_list)} companies")
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
            return False
        
        finally:
            conn.close()
    
    def load_all_stock_data(self):
        print("Starting stock data loading...")
        
        companies = self.download_sp500_companies()
        
        if companies:
            symbols = [comp['symbol'] for comp in companies]
            price_data = self.get_stock_prices_bulk(symbols)
            
            price_dict = {item['symbol']: item for item in price_data}
            
            final_companies = []
            for company in companies:
                symbol = company['symbol']
                if symbol in price_dict:
                    company.update(price_dict[symbol])
                    final_companies.append(company)
            
            if self.load_companies_to_database(final_companies):
                print(f"Successfully loaded {len(final_companies)} companies with live data")
                return True
        
        print("Failed to load stock data")
        return False


def run_stock_data_loader():
    loader = StockDataLoader()
    return loader.load_all_stock_data()


if __name__ == "__main__":
    print("Stock Data Loader - Loading Real Company Data")
    print("=" * 50)
    
    success = run_stock_data_loader()
    
    if success:
        print("Stock data loading completed successfully")
    else:
        print("Stock data loading failed")