"""
Market Data Collector
Fetches real-time and historical OHLCV data from Binance public API
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
from config import settings
from models import MarketData, SessionLocal
import structlog

logger = structlog.get_logger()


class MarketDataCollector:
    """Collects market data from Binance public API"""
    
    def __init__(self):
        """Initialize exchange connection"""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        logger.info("MarketDataCollector initialized", exchange="Binance")
    
    def get_current_price(self, coin: str) -> Optional[float]:
        """
        Get current price for a coin
        
        Args:
            coin: Coin symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Current price in USDT or None if error
        """
        try:
            symbol = f"{coin}/USDT"
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.info("Fetched current price", coin=coin, price=price)
            return price
        except Exception as e:
            logger.error("Error fetching current price", coin=coin, error=str(e))
            return None
    
    def get_ohlcv(
        self, 
        coin: str, 
        timeframe: str, 
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data for a coin
        
        Args:
            coin: Coin symbol (e.g., 'BTC')
            timeframe: Timeframe (15m, 1h, 4h, 1d)
            limit: Number of candles to fetch (default 100)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            symbol = f"{coin}/USDT"
            tf = settings.TIMEFRAME_MAP.get(timeframe, "1h")
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, tf, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['coin'] = coin
            df['timeframe'] = timeframe
            
            logger.info(
                "Fetched OHLCV data", 
                coin=coin, 
                timeframe=timeframe, 
                rows=len(df)
            )
            
            return df
        
        except Exception as e:
            logger.error(
                "Error fetching OHLCV data", 
                coin=coin, 
                timeframe=timeframe, 
                error=str(e)
            )
            return None
    
    def get_historical_ohlcv(
        self,
        coin: str,
        timeframe: str,
        days: int = 180
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data for ML training
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            days: Number of days to fetch
            
        Returns:
            DataFrame with historical OHLCV data
        """
        try:
            symbol = f"{coin}/USDT"
            tf = settings.TIMEFRAME_MAP.get(timeframe, "1h")
            
            # Calculate how many candles we need
            timeframe_minutes = {
                "1s": 1/60,
                "1m": 1,
                "3m": 3,
                "5m": 5,
                "15m": 15,
                "30m": 30,
                "1h": 60,
                "2h": 120,
                "4h": 240,
                "6h": 360,
                "8h": 480,
                "12h": 720,
                "1d": 1440,
                "3d": 4320,
                "1w": 10080,
                "1M": 43200
            }
            minutes = timeframe_minutes.get(timeframe, 60)
            total_candles = int((days * 24 * 60) / minutes)
            
            # Binance API limit is 1000 candles per request
            limit_per_request = 1000
            all_data = []
            
            # Fetch in batches
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            while len(all_data) < total_candles:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    tf, 
                    since=since, 
                    limit=limit_per_request
                )
                
                if not ohlcv:
                    break
                
                all_data.extend(ohlcv)
                
                # Update since to last timestamp
                since = ohlcv[-1][0] + 1
                
                # Rate limiting
                time.sleep(settings.API_RATE_LIMIT_SECONDS)
                
                logger.info(
                    "Fetched historical batch",
                    coin=coin,
                    total_candles=len(all_data)
                )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['coin'] = coin
            df['timeframe'] = timeframe
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(
                "Fetched historical OHLCV data",
                coin=coin,
                timeframe=timeframe,
                days=days,
                rows=len(df)
            )
            
            return df
        
        except Exception as e:
            logger.error(
                "Error fetching historical data",
                coin=coin,
                error=str(e)
            )
            return None
    
    def save_to_db(self, df: pd.DataFrame, table: str = "market_data"):
        """
        Save OHLCV data to database
        
        Args:
            df: DataFrame with OHLCV data
            table: Table name (market_data or historical_data)
        """
        try:
            db = SessionLocal()
            
            for _, row in df.iterrows():
                data = MarketData(
                    coin=row['coin'],
                    timeframe=row['timeframe'],
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                )
                db.add(data)
            
            db.commit()
            logger.info("Saved to database", table=table, rows=len(df))
            
        except Exception as e:
            logger.error("Error saving to database", error=str(e))
            db.rollback()
        finally:
            db.close()
    
    def validate_coin(self, coin: str) -> bool:
        """
        Validate if coin is supported
        
        Args:
            coin: Coin symbol
            
        Returns:
            True if supported, False otherwise
        """
        return coin.upper() in settings.SUPPORTED_COINS
    
    def get_all_coins_data(self, timeframe: str = "1h") -> Dict[str, pd.DataFrame]:
        """
        Get current data for all supported coins
        
        Args:
            timeframe: Timeframe to fetch
            
        Returns:
            Dictionary of coin -> DataFrame
        """
        all_data = {}
        
        for coin in settings.SUPPORTED_COINS:
            df = self.get_ohlcv(coin, timeframe, limit=100)
            if df is not None:
                all_data[coin] = df
            time.sleep(settings.API_RATE_LIMIT_SECONDS)
        
        logger.info("Fetched all coins data", coins=len(all_data))
        return all_data


# Usage example
if __name__ == "__main__":
    collector = MarketDataCollector()
    
    # Get current price
    btc_price = collector.get_current_price("BTC")
    print(f"BTC Price: ${btc_price:,.2f}")
    
    # Get OHLCV data
    df = collector.get_ohlcv("BTC", "1h", limit=50)
    print(df.head())
