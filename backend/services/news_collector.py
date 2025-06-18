import requests
import feedparser
from datetime import datetime, timedelta
from backend.database import DatabaseManager
import time
import re

class NewsCollector:
    def __init__(self):
        self.db = DatabaseManager()
        # Real RSS feeds from major financial news sources
        self.news_sources = [
            {
                'url': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'source': 'Yahoo Finance',
                'category': 'Market'
            },
            {
                'url': 'https://feeds.marketwatch.com/marketwatch/topstories',
                'source': 'MarketWatch',
                'category': 'Market'
            },
            {
                'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'source': 'CNBC',
                'category': 'Business'
            },
            {
                'url': 'https://www.reuters.com/business/finance/rss',
                'source': 'Reuters',
                'category': 'Finance'
            },
            {
                'url': 'https://feeds.bloomberg.com/markets/news.rss',
                'source': 'Bloomberg',
                'category': 'Markets'
            }
        ]
    
    def clean_content(self, content):
        """Clean HTML tags and extra whitespace from content"""
        if not content:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub('<.*?>', '', content)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        # Limit length
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        return clean_text
    
    def get_sentiment_score(self, title, content):
        """Simple sentiment analysis based on keywords"""
        text = (title + " " + content).lower()
        
        positive_words = ['gain', 'rise', 'up', 'bull', 'profit', 'growth', 'surge', 'rally', 'positive', 'strong', 'boost', 'increase']
        negative_words = ['fall', 'drop', 'down', 'bear', 'loss', 'decline', 'crash', 'plunge', 'negative', 'weak', 'decrease', 'concern']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            return max(0.2, 0.5 - (negative_count - positive_count) * 0.1)
        else:
            return 0.5
    
    def collect_real_news(self):
        """Collect real financial news from RSS feeds"""
        conn = self.db.get_connection()
        if not conn:
            print(" Database connection failed!")
            return False
        
        cursor = conn.cursor()
        news_added = 0
        
        try:
            for source_info in self.news_sources:
                try:
                    print(f"Fetching news from {source_info['source']}...")
                    
                    # Parse RSS feed
                    feed = feedparser.parse(source_info['url'])
                    print(f"Found {len(feed.entries)} articles from {source_info['source']}")
                    
                    # Process each news item
                    processed = 0
                    for entry in feed.entries[:10]:  # Limit to 10 latest articles per source
                        title = entry.title if hasattr(entry, 'title') else 'No Title'
                        
                        # Get content
                        content = ""
                        if hasattr(entry, 'description'):
                            content = self.clean_content(entry.description)
                        elif hasattr(entry, 'summary'):
                            content = self.clean_content(entry.summary)
                        
                        print(f"🔍 Processing: '{title[:50]}...' (Content length: {len(content)})")
                        
                        # Skip if no meaningful content
                        if len(content) < 50:
                            print(f" Skipped - content too short ({len(content)} chars)")
                            continue
                        
                        # Get URL
                        url = entry.link if hasattr(entry, 'link') else None
                        
                        # Get author (if available)
                        author = None
                        if hasattr(entry, 'author'):
                            author = entry.author
                        elif hasattr(entry, 'authors') and entry.authors:
                            author = entry.authors[0].get('name', None)
                        
                        # Get published date
                        published_date = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                published_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        
                        # Calculate sentiment
                        sentiment_score = self.get_sentiment_score(title, content)
                        
                        # Check if news already exists (avoid duplicates)
                        cursor.execute("SELECT id FROM News WHERE title = ? AND source = ?", (title, source_info['source']))
                        existing = cursor.fetchone()
                        
                        if not existing:
                            print(f"Adding new article: '{title[:30]}...'")
                            # Insert with correct column names and NULL for stock_symbol
                            cursor.execute("""
                                INSERT INTO News (title, content, source, author, url, 
                                                published_date, stock_symbol, sentiment_score, category)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                title,
                                content,
                                source_info['source'],
                                author,
                                url,
                                published_date,
                                None,  # stock_symbol - NULL for general news
                                sentiment_score,
                                source_info['category']
                            ))
                            news_added += 1
                        else:
                            print(f"⚠️ Duplicate found: '{title[:30]}...' (skipping)")
                        
                        processed += 1
                    
                    print(f" {source_info['source']}: Processed {processed}, Added {news_added}")
                    
                    # Small delay between sources to be respectful
                    time.sleep(1)
                    
                except Exception as e:
                    print(f" Error fetching from {source_info['source']}: {e}")
                    continue
            
            conn.commit()
            print(f"✅ Final result: Successfully added {news_added} new articles")
            return True
            
        except Exception as e:
            print(f" Error collecting news: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def collect_general_news(self):
        """Wrapper method for backward compatibility"""
        return self.collect_real_news()
    
    def get_recent_news(self, limit=20):
        """Get recent financial news"""
        conn = self.db.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT TOP (?) title, content, source, category, 
                       sentiment_score, published_date, url, author
                FROM News 
                ORDER BY published_date DESC
            """, (limit,))
            
            news_list = []
            for row in cursor.fetchall():
                news_list.append({
                    'title': row[0],
                    'content': row[1],
                    'source': row[2],
                    'category': row[3],
                    'sentiment_score': float(row[4]) if row[4] else 0.5,
                    'published_date': row[5],
                    'url': row[6],
                    'author': row[7]
                })
            
            return news_list
            
        except Exception as e:
            print(f"Error getting news: {e}")
            return []
        finally:
            conn.close()
    
    def cleanup_old_news(self, days_old=7):
        """Remove news older than specified days"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM News 
                WHERE published_date < DATEADD(day, -?, GETDATE())
            """, (days_old,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"Cleaned up {deleted_count} old news articles")
            return True
            
        except Exception as e:
            print(f"Error cleaning up news: {e}")
            return False
        finally:
            conn.close()