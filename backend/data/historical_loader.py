"""
Historical Data Loader
Loads and preprocesses historical data for ML training
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime, timedelta
import pandas_ta as ta
from config import settings
from models import HistoricalData, SessionLocal
from data.market_data_collector import MarketDataCollector
import structlog

logger = structlog.get_logger()


class HistoricalDataLoader:
    """Loads and preprocesses historical data for ML training"""
    
    def __init__(self):
        """Initialize data loader"""
        self.collector = MarketDataCollector()
        logger.info("HistoricalDataLoader initialized")
    
    def load_historical_data(
        self,
        coin: str,
        timeframe: str,
        days: int = None
    ) -> Optional[pd.DataFrame]:
        """
        Load historical data for a coin
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            days: Number of days (default from settings)
            
        Returns:
            DataFrame with historical OHLCV data
        """
        if days is None:
            days = settings.HISTORICAL_DAYS
        
        # Try to load from database first
        df = self._load_from_db(coin, timeframe, days)
        
        # If not in DB, fetch from API
        if df is None or len(df) < 100:
            logger.info("Fetching from API", coin=coin, timeframe=timeframe)
            df = self.collector.get_historical_ohlcv(coin, timeframe, days)
            
            if df is not None:
                # Save to database
                self._save_to_db(df)
        
        return df
    
    def _load_from_db(
        self,
        coin: str,
        timeframe: str,
        days: int
    ) -> Optional[pd.DataFrame]:
        """Load historical data from database"""
        try:
            db = SessionLocal()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            results = db.query(HistoricalData).filter(
                HistoricalData.coin == coin,
                HistoricalData.timeframe == timeframe,
                HistoricalData.timestamp >= cutoff_date
            ).order_by(HistoricalData.timestamp).all()
            
            if not results:
                return None
            
            # Convert to DataFrame
            data = [{
                'timestamp': r.timestamp,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume,
                'rsi': r.rsi,
                'ema_fast': r.ema_fast,
                'ema_slow': r.ema_slow,
                'macd': r.macd,
                'macd_signal': r.macd_signal,
                'bollinger_upper': r.bollinger_upper,
                'bollinger_lower': r.bollinger_lower,
                'atr': r.atr
            } for r in results]
            
            df = pd.DataFrame(data)
            df['coin'] = coin
            df['timeframe'] = timeframe
            
            logger.info("Loaded from database", coin=coin, rows=len(df))
            return df
        
        except Exception as e:
            logger.error("Error loading from database", error=str(e))
            return None
        finally:
            db.close()
    
    def _save_to_db(self, df: pd.DataFrame):
        """Save historical data with indicators to database"""
        try:
            db = SessionLocal()
            
            for _, row in df.iterrows():
                data = HistoricalData(
                    coin=row.get('coin'),
                    timeframe=row.get('timeframe'),
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    rsi=row.get('rsi'),
                    ema_fast=row.get('ema_fast'),
                    ema_slow=row.get('ema_slow'),
                    macd=row.get('macd'),
                    macd_signal=row.get('macd_signal'),
                    bollinger_upper=row.get('bollinger_upper'),
                    bollinger_lower=row.get('bollinger_lower'),
                    atr=row.get('atr')
                )
                db.add(data)
            
            db.commit()
            logger.info("Saved historical data to DB", rows=len(df))
        
        except Exception as e:
            logger.error("Error saving to database", error=str(e))
            db.rollback()
        finally:
            db.close()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicators
        """
        try:
            # RSI
            df['rsi'] = ta.rsi(df['close'], length=settings.RSI_PERIOD)
            
            # EMA
            df['ema_fast'] = ta.ema(df['close'], length=settings.EMA_FAST)
            df['ema_slow'] = ta.ema(df['close'], length=settings.EMA_SLOW)
            
            # MACD
            macd = ta.macd(
                df['close'],
                fast=settings.MACD_FAST,
                slow=settings.MACD_SLOW,
                signal=settings.MACD_SIGNAL
            )
            df['macd'] = macd[f'MACD_{settings.MACD_FAST}_{settings.MACD_SLOW}_{settings.MACD_SIGNAL}']
            df['macd_signal'] = macd[f'MACDs_{settings.MACD_FAST}_{settings.MACD_SLOW}_{settings.MACD_SIGNAL}']
            df['macd_hist'] = macd[f'MACDh_{settings.MACD_FAST}_{settings.MACD_SLOW}_{settings.MACD_SIGNAL}']
            
            # Bollinger Bands
            bbands = ta.bbands(
                df['close'],
                length=settings.BOLLINGER_PERIOD,
                std=settings.BOLLINGER_STD
            )
            df['bollinger_upper'] = bbands[f'BBU_{settings.BOLLINGER_PERIOD}_{settings.BOLLINGER_STD}.0']
            df['bollinger_middle'] = bbands[f'BBM_{settings.BOLLINGER_PERIOD}_{settings.BOLLINGER_STD}.0']
            df['bollinger_lower'] = bbands[f'BBL_{settings.BOLLINGER_PERIOD}_{settings.BOLLINGER_STD}.0']
            
            # ATR (Average True Range) for volatility
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            # Volume SMA
            df['volume_sma'] = ta.sma(df['volume'], length=20)
            
            # Price change
            df['price_change'] = df['close'].pct_change()
            df['price_change_abs'] = df['close'].diff()
            
            # Target for ML (1 if price goes up, 0 if down)
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
            
            # Drop NaN values from indicator calculation
            df = df.dropna()
            
            logger.info("Added technical indicators", indicators=8)
            return df
        
        except Exception as e:
            logger.error("Error adding indicators", error=str(e))
            return df
    
    def prepare_ml_dataset(
        self,
        coin: str,
        timeframe: str,
        days: int = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare dataset for ML training
        
        Args:
            coin: Coin symbol
            timeframe: Timeframe
            days: Number of days
            
        Returns:
            Tuple of (train_df, test_df)
        """
        # Load historical data
        df = self.load_historical_data(coin, timeframe, days)
        
        if df is None:
            logger.error("Failed to load historical data")
            return None, None
        
        # Add technical indicators
        df = self.add_technical_indicators(df)
        
        # Split into train/test
        split_idx = int(len(df) * settings.ML_TRAIN_TEST_SPLIT)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
        
        logger.info(
            "Prepared ML dataset",
            coin=coin,
            total_rows=len(df),
            train_rows=len(train_df),
            test_rows=len(test_df)
        )
        
        return train_df, test_df
    
    def get_feature_columns(self) -> list:
        """Get list of feature columns for ML"""
        return [
            'open', 'high', 'low', 'close', 'volume',
            'rsi', 'ema_fast', 'ema_slow',
            'macd', 'macd_signal', 'macd_hist',
            'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
            'atr', 'volume_sma', 'price_change'
        ]


# Usage example
if __name__ == "__main__":
    loader = HistoricalDataLoader()
    
    # Prepare ML dataset
    train_df, test_df = loader.prepare_ml_dataset("BTC", "1h", days=180)
    
    if train_df is not None:
        print(f"Train set: {len(train_df)} rows")
        print(f"Test set: {len(test_df)} rows")
        print(f"\nFeatures: {loader.get_feature_columns()}")
        print(f"\nSample data:\n{train_df.head()}")
