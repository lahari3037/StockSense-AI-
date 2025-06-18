from datetime import datetime

class DataProcessingEngine:
    def __init__(self):
        self.processed_count = 0
        self.news_processed = 0
    
    def process_market_data(self):
        """Process market analytics"""
        self.processed_count += 1
        return {
            'processed_at': datetime.now(),
            'status': 'completed',
            'market_records_processed': self.processed_count
        }
    
    def process_news_sentiment(self):
        """Process news sentiment"""
        self.news_processed += 1
        return {
            'processed_at': datetime.now(), 
            'status': 'completed',
            'news_records_processed': self.news_processed
        }
    
    def get_processing_stats(self):
        """Get processing statistics"""
        return {
            'total_market_processing_runs': self.processed_count,
            'total_news_processing_runs': self.news_processed,
            'last_updated': datetime.now().isoformat()
        }