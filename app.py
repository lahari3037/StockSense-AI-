from flask import Flask, render_template, request, jsonify, session
from backend.database import DatabaseManager
from backend.services.stock_collector import StockCollector
from backend.services.news_collector import NewsCollector
from backend.data_processing.processing_engine import DataProcessingEngine
from backend.services.portfolio_manager import PortfolioManager
from settings import config
import threading
import time
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['ENV'] = 'development'
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

# Initialize services
db_manager = DatabaseManager()
stock_collector = StockCollector()
news_collector = NewsCollector()
portfolio_manager = PortfolioManager()
processor = DataProcessingEngine()  # ADD: Initialize data processor

# Fixed timing intervals (in seconds)
PRICE_UPDATE_INTERVAL = 300  # 5 minutes
NEWS_UPDATE_INTERVAL = 600   # 10 minutes

# Routes
@app.route('/')
def dashboard():
    """Main dashboard with market overview"""
    return render_template('dashboard.html')

@app.route('/portfolio')
def portfolio():
    """Portfolio management page"""
    return render_template('portfolio.html')

# API Routes
@app.route('/api/stocks/prices')
def get_stock_prices():
    """Get current stock prices"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP (50) symbol, company_name, current_price, 
                   price_change, price_change_percent, volume, sector
            FROM Stocks 
            WHERE current_price > 0
            ORDER BY price_change_percent DESC
        """)
        
        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'symbol': row[0],
                'company_name': row[1],
                'current_price': float(row[2]) if row[2] else 0,
                'price_change': float(row[3]) if row[3] else 0,
                'price_change_percent': float(row[4]) if row[4] else 0,
                'volume': row[5] if row[5] else 0,
                'sector': row[6]
            })
        
        conn.close()
        return jsonify(stocks)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks/movers')
def get_top_movers():
    """Get top gaining and losing stocks"""
    movers = stock_collector.get_top_movers(10)
    return jsonify(movers)

@app.route('/api/stocks/search')
def search_stocks():
    """Search stocks by symbol or company name"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, company_name, current_price, sector
            FROM Stocks 
            WHERE symbol LIKE ? OR company_name LIKE ?
            ORDER BY symbol
        """, (f'%{query}%', f'%{query}%'))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'symbol': row[0],
                'company_name': row[1],
                'current_price': float(row[2]) if row[2] else 0,
                'sector': row[3]
            })
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/<int:user_id>')
def get_portfolio(user_id):
    """Get user portfolio"""
    portfolio_data = portfolio_manager.get_portfolio_summary(user_id)
    if portfolio_data:
        return jsonify(portfolio_data)
    else:
        return jsonify({'error': 'Portfolio not found'}), 404

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    """Add stock to portfolio"""
    data = request.json
    
    required_fields = ['user_id', 'symbol', 'quantity', 'purchase_price']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    success = portfolio_manager.add_stock_position(
        data['user_id'],
        data['symbol'].upper(),
        data['quantity'],
        data['purchase_price']
    )
    
    if success:
        return jsonify({'message': 'Stock added to portfolio successfully'})
    else:
        return jsonify({'error': 'Failed to add stock to portfolio'}), 500

@app.route('/api/portfolio/allocation/<int:user_id>')
def get_portfolio_allocation(user_id):
    """Get portfolio sector allocation"""
    allocation = portfolio_manager.get_sector_allocation(user_id)
    return jsonify(allocation)

@app.route('/api/news')
def get_news():
    """Get recent financial news"""
    news = news_collector.get_recent_news(20)
    return jsonify(news)

@app.route('/api/update-prices', methods=['POST'])
def update_prices():
    """Manually trigger price update"""
    success = stock_collector.update_all_prices()
    if success:
        return jsonify({'message': 'Prices updated successfully'})
    else:
        return jsonify({'error': 'Failed to update prices'}), 500

@app.route('/test')
def test_connection():
    """Test database connection"""
    conn = db_manager.get_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'Database connection successful'})
    else:
        return jsonify({'status': 'Database connection failed'})

# ADD: New API endpoint for processing stats
@app.route('/api/processing/stats')
def get_processing_stats():
    """Get data processing statistics"""
    stats = processor.get_processing_stats()
    return jsonify(stats)

# UPDATED: Background task for automatic price updates (every 5 minutes)
def background_price_updater():
    """Background thread to update prices every 5 minutes"""
    while True:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f" [{current_time}] Starting automatic price update...")
            
            # EXISTING: Stock price collection
            stock_collector.update_all_prices()
            
            # ADD: Data processing step
            print(f" [{current_time}] Processing market analytics...")
            analytics = processor.process_market_data()
            print(f"[{current_time}] Analytics processed")
            
            print(f"[{current_time}] Price update completed")
            print(f"Sleeping for {PRICE_UPDATE_INTERVAL//60} minutes...")
            
        except Exception as e:
            print(f"Error in background price update: {e}")
        
        # FIXED: Sleep for exactly 5 minutes (300 seconds)
        time.sleep(300) 

# UPDATED: Background task for news collection (every 10 minutes)
def background_news_collector():
    """Background thread to collect news every 10 minutes"""
    while True:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] Collecting financial news...")
            
            # EXISTING: News collection
            news_collector.collect_general_news()
            
            # ADD: News processing step
            print(f" [{current_time}] Processing news sentiment...")
            news_analytics = processor.process_news_sentiment()
            print(f"[{current_time}] News processing completed")
            
            print(f" [{current_time}] News collection completed")
            print(f" Sleeping for {NEWS_UPDATE_INTERVAL//60} minutes...")
            
        except Exception as e:
            print(f"Error in background news collection: {e}")
        
        # FIXED: Sleep for exactly 10 minutes (600 seconds)
        time.sleep(600) 

# Start background tasks
def start_background_tasks():
    print(" Starting background tasks...")
    print(f" Stock updates: every {PRICE_UPDATE_INTERVAL//60} minutes")
    print(f"News updates: every {NEWS_UPDATE_INTERVAL//60} minutes")
    print(f" Data processing: integrated with each update")
    
    # Start price updater thread
    price_thread = threading.Thread(target=background_price_updater)
    price_thread.daemon = True
    price_thread.start()
    print(" Price updater thread started")
    
    # Start news collector thread  
    news_thread = threading.Thread(target=background_news_collector)
    news_thread.daemon = True
    news_thread.start()
    print(" News collector thread started")

if __name__ == '__main__':
    print("FinanceAI Server Starting...")
    
    # Initialize sample news on startup (one time)
    print("Initial news collection...")
    news_collector.collect_general_news()
    
    # Start background tasks
    start_background_tasks()
    
    print("FinanceAI Server Started!")
    print(" Dashboard: http://localhost:5000")
    print(" Portfolio: http://localhost:5000/portfolio")
    print(" Test Connection: http://localhost:5000/test")
    print(" Processing Stats: http://localhost:5000/api/processing/stats")
    print("* Debugger is active!")
    
    app.run(debug=False, host='0.0.0.0', port=5000)