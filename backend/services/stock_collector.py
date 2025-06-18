import yfinance as yf
import time
from datetime import datetime
from backend.database import DatabaseManager
from settings import config

class StockCollector:
    def __init__(self):
        self.db = DatabaseManager()
    
    def update_single_stock(self, symbol):
        """Update price data for a single stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = info.get('currentPrice', 0)
            if not current_price:
                current_price = info.get('regularMarketPrice', 0)
            
            price_change = info.get('regularMarketChange', 0)
            change_percent = info.get('regularMarketChangePercent', 0)
            volume = info.get('regularMarketVolume', 0)
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 0)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_change': price_change,
                'change_percent': change_percent,
                'volume': volume,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio
            }
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def update_all_prices(self):
        """Update prices for all stocks in database"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        updated_count = 0
        
        try:
            # Get all stock symbols
            cursor.execute("SELECT symbol FROM Stocks")
            symbols = [row[0] for row in cursor.fetchall()]
            
            print(f"Updating prices for {len(symbols)} stocks...")
            
            for symbol in symbols:
                stock_data = self.update_single_stock(symbol)
                
                if stock_data:
                    cursor.execute("""
                        UPDATE Stocks 
                        SET current_price = ?, 
                            price_change = ?, 
                            price_change_percent = ?,
                            volume = ?,
                            market_cap = ?,
                            pe_ratio = ?,
                            last_updated = GETDATE()
                        WHERE symbol = ?
                    """, (
                        stock_data['current_price'],
                        stock_data['price_change'],
                        stock_data['change_percent'],
                        stock_data['volume'],
                        stock_data['market_cap'],
                        stock_data['pe_ratio'],
                        symbol
                    ))
                    updated_count += 1
                
                # Small delay to avoid rate limiting
                time.sleep(config.STOCK_API_DELAY)
            
            conn.commit()
            print(f"Successfully updated {updated_count} stocks")
            return True
            
        except Exception as e:
            print(f"Error updating prices: {e}")
            return False
        finally:
            conn.close()
    
    def get_top_movers(self, limit=20):
        """Get top gaining and losing stocks"""
        conn = self.db.get_connection()
        if not conn:
            return {'gainers': [], 'losers': []}
        
        cursor = conn.cursor()
        
        try:
            # Top gainers
            cursor.execute("""
                SELECT TOP (?) symbol, company_name, current_price, 
                       price_change_percent
                FROM Stocks 
                WHERE current_price > 0 AND price_change_percent IS NOT NULL
                ORDER BY price_change_percent DESC
            """, (limit,))
            
            gainers = []
            for row in cursor.fetchall():
                gainers.append({
                    'symbol': row[0],
                    'company_name': row[1],
                    'current_price': float(row[2]),
                    'change_percent': float(row[3])
                })
            
            # Top losers
            cursor.execute("""
                SELECT TOP (?) symbol, company_name, current_price, 
                       price_change_percent
                FROM Stocks 
                WHERE current_price > 0 AND price_change_percent IS NOT NULL
                ORDER BY price_change_percent ASC
            """, (limit,))
            
            losers = []
            for row in cursor.fetchall():
                losers.append({
                    'symbol': row[0],
                    'company_name': row[1],
                    'current_price': float(row[2]),
                    'change_percent': float(row[3])
                })
            
            return {'gainers': gainers, 'losers': losers}
            
        except Exception as e:
            print(f"Error getting top movers: {e}")
            return {'gainers': [], 'losers': []}
        finally:
            conn.close()