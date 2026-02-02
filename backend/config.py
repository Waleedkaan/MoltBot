"""
MoltBot Configuration
Central configuration for all system parameters
"""
from pydantic_settings import BaseSettings
from typing import List, Dict
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "MoltBot Trading Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Supported Coins (20 major cryptocurrencies)
    SUPPORTED_COINS: List[str] = [
        "BTC", "ETH", "BNB", "SOL", "XRP", 
        "ADA", "DOGE", "AVAX", "DOT", "TRX",
        "MATIC", "LTC", "LINK", "UNI", "ATOM",
        "NEAR", "ICP", "FIL", "APT", "ARB"
    ]
    
    # Timeframes
    TIMEFRAMES: List[str] = [
        "1s", "1m", "3m", "5m", "15m", "30m", 
        "1h", "2h", "4h", "6h", "8h", "12h", 
        "1d", "3d", "1w", "1M"
    ]
    
    # Timeframe mapping for Binance API
    TIMEFRAME_MAP: Dict[str, str] = {
        "1s": "1s",
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M"
    }
    
    # Prediction Weights
    STRATEGY_WEIGHT: float = 0.40  # 40%
    ML_WEIGHT: float = 0.35        # 35%
    NEWS_WEIGHT: float = 0.25      # 25%
    
    # Confidence Thresholds
    MIN_CONFIDENCE_THRESHOLD: int = 60  # Minimum confidence to show signal
    HIGH_CONFIDENCE_THRESHOLD: int = 75  # High confidence threshold
    
    # Risk Management (for auto-trade)
    MAX_TRADE_RISK_PERCENT: float = 2.0  # Max 2% of portfolio per trade
    DEFAULT_STOP_LOSS_PERCENT: float = 3.0  # 3% stop loss
    DEFAULT_TAKE_PROFIT_PERCENT: float = 5.0  # 5% take profit
    
    # Data Sources
    BINANCE_API_URL: str = "https://api.binance.com"
    CRYPTOPANIC_API_URL: str = "https://cryptopanic.com/api/v1"
    FEAR_GREED_API_URL: str = "https://api.alternative.me/fng/"
    
    # API Keys (optional, from .env)
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    CRYPTOPANIC_API_KEY: str = "free"  # Free tier
    
    # Database
    DATABASE_URL: str = "sqlite:///./data_storage/moltbot.db"
    
    # Historical Data Settings
    HISTORICAL_DAYS: int = 180  # 6 months for ML training
    ML_TRAIN_TEST_SPLIT: float = 0.8  # 80% train, 20% test
    
    # Strategy Parameters
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: int = 70
    RSI_OVERSOLD: int = 30
    
    EMA_FAST: int = 9
    EMA_SLOW: int = 21
    
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: int = 2
    
    VOLUME_SPIKE_MULTIPLIER: float = 2.0  # 2x average volume
    
    # ML Model Settings
    ML_MODELS: List[str] = ["logistic_regression", "random_forest", "xgboost", "lstm"]
    MODEL_RETRAIN_DAYS: int = 7  # Retrain models weekly
    
    # Sentiment Analysis
    SENTIMENT_LOOKBACK_HOURS: int = 24  # Look back 24 hours for news
    
    # Rate Limiting
    API_RATE_LIMIT_SECONDS: int = 1  # Wait 1 second between API calls
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# Coin display names
COIN_DISPLAY_NAMES: Dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "BNB": "Binance Coin",
    "SOL": "Solana",
    "XRP": "Ripple",
    "ADA": "Cardano",
    "DOGE": "Dogecoin",
    "AVAX": "Avalanche",
    "DOT": "Polkadot",
    "TRX": "Tron",
    "MATIC": "Polygon",
    "LTC": "Litecoin",
    "LINK": "Chainlink",
    "UNI": "Uniswap",
    "ATOM": "Cosmos",
    "NEAR": "NEAR Protocol",
    "ICP": "Internet Computer",
    "FIL": "Filecoin",
    "APT": "Aptos",
    "ARB": "Arbitrum"
}


# Default user settings
DEFAULT_USER_SETTINGS = {
    "mode": "prediction",  # "prediction" or "auto_trade"
    "coin": "BTC",
    "timeframe": "1h",
    "confidence_threshold": 60,
    "visible_sections": {
        "strategy": True,
        "ml": True,
        "news": True,
        "final": True,
        "predicted_price": True
    },
    "enabled_strategies": {
        "rsi": True,
        "ema_crossover": True,
        "macd": True,
        "bollinger": True,
        "volume_spike": True,
        "support_resistance": True
    }
}
