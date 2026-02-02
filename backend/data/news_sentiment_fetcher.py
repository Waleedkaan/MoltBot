"""
News & Sentiment Fetcher
Fetches news and sentiment data from multiple free sources
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from textblob import TextBlob
from config import settings
from models import NewsSentiment, SessionLocal
import structlog

logger = structlog.get_logger()


class NewsSentimentFetcher:
    """Fetches news and sentiment data from free sources"""
    
    def __init__(self):
        """Initialize sentiment fetcher"""
        self.cryptopanic_api = settings.CRYPTOPANIC_API_URL
        self.fear_greed_api = settings.FEAR_GREED_API_URL
        logger.info("NewsSentimentFetcher initialized")
    
    def get_fear_greed_index(self) -> Optional[Dict]:
        """
        Get Fear & Greed Index
        
        Returns:
            Dictionary with fear/greed data
        """
        try:
            response = requests.get(self.fear_greed_api, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                fg_data = data['data'][0]
                value = int(fg_data['value'])
                classification = fg_data['value_classification']
                
                # Convert to sentiment score (-1 to 1)
                # Fear & Greed is 0-100, where 0 = Extreme Fear, 100 = Extreme Greed
                sentiment_score = (value - 50) / 50  # Normalize to -1 to 1
                
                # Confidence based on extreme values
                confidence = min(100, abs(value - 50) * 2)
                
                result = {
                    'value': value,
                    'classification': classification,
                    'sentiment_score': sentiment_score,
                    'confidence': confidence,
                    'timestamp': datetime.now()
                }
                
                logger.info(
                    "Fetched Fear & Greed Index",
                    value=value,
                    classification=classification
                )
                
                return result
        
        except Exception as e:
            logger.error("Error fetching Fear & Greed Index", error=str(e))
            return None
    
    def get_cryptopanic_news(
        self,
        coin: str = None,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get news from CryptoPanic
        
        Args:
            coin: Specific coin filter (optional)
            hours: Lookback hours (default 24)
            
        Returns:
            List of news items with sentiment
        """
        try:
            # CryptoPanic free API endpoint
            url = f"{self.cryptopanic_api}/posts/"
            
            params = {
                'auth_token': settings.CRYPTOPANIC_API_KEY,
                'public': 'true'
            }
            
            # Filter by coin if specified
            if coin:
                # Map common coin symbols to CryptoPanic currencies
                currency_map = {
                    'BTC': 'BTC',
                    'ETH': 'ETH',
                    'BNB': 'BNB',
                    'SOL': 'SOL',
                    'XRP': 'XRP',
                    'ADA': 'ADA',
                    'DOGE': 'DOGE',
                    'AVAX': 'AVAX',
                    'DOT': 'DOT',
                    'MATIC': 'MATIC'
                }
                
                if coin in currency_map:
                    params['currencies'] = currency_map[coin]
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            news_items = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            if 'results' in data:
                for item in data['results']:
                    published_at = datetime.fromisoformat(
                        item['published_at'].replace('Z', '+00:00')
                    )
                    
                    # Filter by time
                    if published_at < cutoff_time:
                        continue
                    
                    title = item.get('title', '')
                    
                    # Analyze sentiment
                    sentiment = self._analyze_text_sentiment(title)
                    
                    news_item = {
                        'title': title,
                        'url': item.get('url', ''),
                        'published_at': published_at,
                        'source': item.get('source', {}).get('title', 'Unknown'),
                        'sentiment_score': sentiment['score'],
                        'confidence': sentiment['confidence']
                    }
                    
                    news_items.append(news_item)
            
            logger.info(
                "Fetched CryptoPanic news",
                coin=coin,
                count=len(news_items)
            )
            
            return news_items
        
        except Exception as e:
            logger.error("Error fetching CryptoPanic news", error=str(e))
            return []
    
    def _analyze_text_sentiment(self, text: str) -> Dict:
        """
        Analyze text sentiment using TextBlob
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and confidence
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Confidence based on subjectivity (more subjective = higher confidence)
            confidence = min(100, subjectivity * 100)
            
            # Ensure minimum confidence
            if confidence < 20:
                confidence = 20
            
            return {
                'score': polarity,
                'confidence': confidence
            }
        
        except Exception as e:
            logger.error("Error analyzing sentiment", error=str(e))
            return {'score': 0.0, 'confidence': 0}
    
    def get_aggregated_sentiment(
        self,
        coin: str,
        hours: int = 24
    ) -> Optional[Dict]:
        """
        Get aggregated sentiment for a coin from all sources
        
        Args:
            coin: Coin symbol
            hours: Lookback hours
            
        Returns:
            Aggregated sentiment data
        """
        try:
            sentiments = []
            
            # Fear & Greed Index (general market sentiment)
            fg_index = self.get_fear_greed_index()
            if fg_index:
                sentiments.append({
                    'score': fg_index['sentiment_score'],
                    'confidence': fg_index['confidence'] * 0.3,  # Weight 30%
                    'source': 'fear_greed'
                })
            
            # CryptoPanic news
            news = self.get_cryptopanic_news(coin, hours)
            if news:
                # Average news sentiment
                news_scores = [n['sentiment_score'] for n in news if n['sentiment_score'] != 0]
                if news_scores:
                    avg_score = sum(news_scores) / len(news_scores)
                    avg_confidence = sum([n['confidence'] for n in news]) / len(news)
                    
                    sentiments.append({
                        'score': avg_score,
                        'confidence': avg_confidence * 0.7,  # Weight 70%
                        'source': 'cryptopanic'
                    })
            
            # Calculate weighted average
            if sentiments:
                total_weight = sum(s['confidence'] for s in sentiments)
                
                if total_weight > 0:
                    weighted_score = sum(
                        s['score'] * s['confidence'] for s in sentiments
                    ) / total_weight
                    
                    avg_confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)
                    
                    # Convert sentiment score to signal
                    if weighted_score > 0.2:
                        signal = "BUY"
                    elif weighted_score < -0.2:
                        signal = "SELL"
                    else:
                        signal = "NEUTRAL"
                    
                    result = {
                        'coin': coin,
                        'sentiment_score': weighted_score,
                        'confidence': round(avg_confidence, 2),
                        'signal': signal,
                        'num_sources': len(sentiments),
                        'timestamp': datetime.now()
                    }
                    
                    # Save to database
                    self._save_to_db(coin, result)
                    
                    logger.info(
                        "Aggregated sentiment",
                        coin=coin,
                        signal=signal,
                        confidence=result['confidence']
                    )
                    
                    return result
            
            # Default neutral if no data
            return {
                'coin': coin,
                'sentiment_score': 0.0,
                'confidence': 0,
                'signal': 'NEUTRAL',
                'num_sources': 0,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error("Error aggregating sentiment", coin=coin, error=str(e))
            return None
    
    def _save_to_db(self, coin: str, sentiment_data: Dict):
        """Save sentiment data to database"""
        try:
            db = SessionLocal()
            
            sentiment = NewsSentiment(
                coin=coin,
                timestamp=sentiment_data['timestamp'],
                source='aggregated',
                title=f"Aggregated sentiment from {sentiment_data['num_sources']} sources",
                content='',
                sentiment_score=sentiment_data['sentiment_score'],
                confidence=sentiment_data['confidence']
            )
            
            db.add(sentiment)
            db.commit()
            logger.info("Saved sentiment to DB", coin=coin)
        
        except Exception as e:
            logger.error("Error saving sentiment to DB", error=str(e))
            db.rollback()
        finally:
            db.close()


# Usage example
if __name__ == "__main__":
    fetcher = NewsSentimentFetcher()
    
    # Get Fear & Greed Index
    fg = fetcher.get_fear_greed_index()
    if fg:
        print(f"\nFear & Greed Index: {fg['value']} ({fg['classification']})")
    
    # Get aggregated sentiment for BTC
    sentiment = fetcher.get_aggregated_sentiment("BTC", hours=24)
    if sentiment:
        print(f"\nBTC Sentiment:")
        print(f"  Signal: {sentiment['signal']}")
        print(f"  Confidence: {sentiment['confidence']}%")
        print(f"  Score: {sentiment['sentiment_score']:.3f}")
