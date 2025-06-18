from backend.database import DatabaseManager
from settings import config

def add_sample_portfolio():
    """Add sample portfolio data for testing"""
    
    db = DatabaseManager()
    conn = db.get_connection()
    if not conn:
        print("Database connection failed")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Create test user first
        cursor.execute("""
            IF NOT EXISTS (SELECT id FROM [Users] WHERE id = 1)
            INSERT INTO [Users] (username, email, password_hash, first_name)
            VALUES ('testuser', 'test@example.com', 'test123', 'Test User')
        """)
        
        # Sample portfolio - realistic stock purchases
        sample_positions = [
            {'symbol': 'AAPL', 'quantity': 15, 'purchase_price': 145.50},
            {'symbol': 'GOOGL', 'quantity': 3, 'purchase_price': 2420.00},
            {'symbol': 'MSFT', 'quantity': 8, 'purchase_price': 310.25},
            {'symbol': 'TSLA', 'quantity': 5, 'purchase_price': 890.00},
            {'symbol': 'AMZN', 'quantity': 4, 'purchase_price': 3100.00},
            {'symbol': 'NVDA', 'quantity': 6, 'purchase_price': 220.00},
            {'symbol': 'META', 'quantity': 7, 'purchase_price': 280.00},
            {'symbol': 'NFLX', 'quantity': 3, 'purchase_price': 450.00}
        ]
        
        user_id = 1
        
        # Clear existing portfolio for test user
        cursor.execute("DELETE FROM Portfolio WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM Transactions WHERE user_id = ?", (user_id,))
        
        # Add each position
        for position in sample_positions:
            symbol = position['symbol']
            quantity = position['quantity']
            purchase_price = position['purchase_price']
            total_amount = quantity * purchase_price
            
            # Check if stock exists in our database
            cursor.execute("SELECT symbol FROM Stocks WHERE symbol = ?", (symbol,))
            if cursor.fetchone():
                
                # Add to portfolio
                cursor.execute("""
                    INSERT INTO Portfolio (user_id, stock_symbol, quantity, purchase_price)
                    VALUES (?, ?, ?, ?)
                """, (user_id, symbol, quantity, purchase_price))
                
                # Add transaction record
                cursor.execute("""
                    INSERT INTO Transactions (user_id, stock_symbol, transaction_type, 
                                            quantity, price, total_amount)
                    VALUES (?, ?, 'BUY', ?, ?, ?)
                """, (user_id, symbol, quantity, purchase_price, total_amount))
                
                print(f"Added {quantity} shares of {symbol} at ${purchase_price}")
            else:
                print(f"Stock {symbol} not found in database, skipping...")
        
        conn.commit()
        print("\n Sample portfolio created successfully!")
        print("Portfolio contains stocks worth approximately $50,000")
        print("Visit http://localhost:5000/portfolio to see your test portfolio")
        
        return True
        
    except Exception as e:
        print(f"Error creating sample portfolio: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Creating Sample Portfolio for Testing...")
    print("=" * 40)
    add_sample_portfolio()