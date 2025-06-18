from backend.database import DatabaseManager
from backend.services.stock_collector import StockCollector
from settings import config

class PortfolioManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.stock_collector = StockCollector()
    
    def add_stock_position(self, user_id, symbol, quantity, purchase_price):
        """Add a new stock position to portfolio"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            # Check if stock exists in our database
            cursor.execute("SELECT symbol FROM Stocks WHERE symbol = ?", (symbol,))
            if not cursor.fetchone():
                return False
            
            # Add to portfolio
            cursor.execute("""
                INSERT INTO Portfolio (user_id, stock_symbol, quantity, purchase_price)
                VALUES (?, ?, ?, ?)
            """, (user_id, symbol, quantity, purchase_price))
            
            # Add transaction record
            total_amount = quantity * purchase_price
            cursor.execute("""
                INSERT INTO Transactions (user_id, stock_symbol, transaction_type, 
                                        quantity, price, total_amount)
                VALUES (?, ?, 'BUY', ?, ?, ?)
            """, (user_id, symbol, quantity, purchase_price, total_amount))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error adding stock position: {e}")
            return False
        finally:
            conn.close()
    
    def get_portfolio_summary(self, user_id):
        """Get complete portfolio summary with calculations"""
        conn = self.db.get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.stock_symbol, p.quantity, p.purchase_price, 
                       s.company_name, s.current_price, s.sector,
                       p.purchase_date
                FROM Portfolio p
                JOIN Stocks s ON p.stock_symbol = s.symbol
                WHERE p.user_id = ?
                ORDER BY p.purchase_date DESC
            """, (user_id,))
            
            holdings = []
            total_invested = 0
            total_current_value = 0
            
            for row in cursor.fetchall():
                symbol = row[0]
                quantity = row[1]
                purchase_price = float(row[2])
                current_price = float(row[4]) if row[4] else purchase_price
                
                invested = quantity * purchase_price
                current_value = quantity * current_price
                gain_loss = current_value - invested
                gain_loss_percent = (gain_loss / invested) * 100 if invested > 0 else 0
                
                holdings.append({
                    'symbol': symbol,
                    'company_name': row[3],
                    'sector': row[5],
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'current_price': current_price,
                    'invested_amount': invested,
                    'current_value': current_value,
                    'gain_loss': gain_loss,
                    'gain_loss_percent': gain_loss_percent,
                    'purchase_date': row[6]
                })
                
                total_invested += invested
                total_current_value += current_value
            
            total_gain_loss = total_current_value - total_invested
            total_gain_loss_percent = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
            
            return {
                'holdings': holdings,
                'summary': {
                    'total_invested': total_invested,
                    'total_current_value': total_current_value,
                    'total_gain_loss': total_gain_loss,
                    'total_gain_loss_percent': total_gain_loss_percent,
                    'number_of_positions': len(holdings)
                }
            }
            
        except Exception as e:
            print(f"Error getting portfolio summary: {e}")
            return None
        finally:
            conn.close()
    
    def get_sector_allocation(self, user_id):
        """Get portfolio allocation by sector"""
        conn = self.db.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT s.sector, 
                       SUM(p.quantity * s.current_price) as sector_value,
                       COUNT(*) as stock_count
                FROM Portfolio p
                JOIN Stocks s ON p.stock_symbol = s.symbol
                WHERE p.user_id = ? AND s.current_price > 0
                GROUP BY s.sector
                ORDER BY sector_value DESC
            """, (user_id,))
            
            allocation = []
            total_value = 0
            
            # Calculate total value first
            for row in cursor.fetchall():
                total_value += float(row[1])
            
            # Reset cursor and calculate percentages
            cursor.execute("""
                SELECT s.sector, 
                       SUM(p.quantity * s.current_price) as sector_value,
                       COUNT(*) as stock_count
                FROM Portfolio p
                JOIN Stocks s ON p.stock_symbol = s.symbol
                WHERE p.user_id = ? AND s.current_price > 0
                GROUP BY s.sector
                ORDER BY sector_value DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
                sector_value = float(row[1])
                percentage = (sector_value / total_value) * 100 if total_value > 0 else 0
                
                allocation.append({
                    'sector': row[0],
                    'value': sector_value,
                    'percentage': percentage,
                    'stock_count': row[2]
                })
            
            return allocation
            
        except Exception as e:
            print(f"Error getting sector allocation: {e}")
            return []
        finally:
            conn.close()