"""
Database Models
SQLAlchemy ORM models for data persistence
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()


class MarketData(Base):
    """OHLCV market data"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    coin = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class HistoricalData(Base):
    """Historical OHLCV for ML training"""
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    coin = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    # Technical indicators (calculated)
    rsi = Column(Float)
    ema_fast = Column(Float)
    ema_slow = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_lower = Column(Float)
    atr = Column(Float)


class NewsSentiment(Base):
    """News and sentiment data"""
    __tablename__ = "news_sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    coin = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    source = Column(String, nullable=False)  # cryptopanic, twitter, fear_greed
    title = Column(String)
    content = Column(String)
    sentiment_score = Column(Float, nullable=False)  # -1 to 1
    confidence = Column(Float, nullable=False)  # 0 to 100
    url = Column(String)


class UserSettings(Base):
    """User preferences and settings"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default", unique=True)
    mode = Column(String, default="prediction")  # prediction or auto_trade
    coin = Column(String, default="BTC")
    timeframe = Column(String, default="1h")
    confidence_threshold = Column(Integer, default=60)
    visible_sections = Column(JSON)  # {strategy: true, ml: true, ...}
    enabled_strategies = Column(JSON)  # {rsi: true, ema: true, ...}
    # Auto-trade settings
    api_key_encrypted = Column(String)
    max_trade_risk = Column(Float, default=2.0)
    stop_loss_percent = Column(Float, default=3.0)
    take_profit_percent = Column(Float, default=5.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeHistory(Base):
    """Trade execution history (for auto-trade mode)"""
    __tablename__ = "trade_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    coin = Column(String, nullable=False)
    signal = Column(String, nullable=False)  # BUY or SELL
    confidence = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    quantity = Column(Float, nullable=False)
    status = Column(String, default="open")  # open, closed, stopped
    exit_price = Column(Float)
    profit_loss = Column(Float)
    exit_timestamp = Column(DateTime)
    notes = Column(String)


class Prediction(Base):
    """Prediction history for analysis"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    coin = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Strategy signals
    strategy_signal = Column(String)  # BUY/SELL/NEUTRAL
    strategy_confidence = Column(Float)
    strategy_details = Column(JSON)  # Individual strategy results
    
    # ML predictions
    ml_signal = Column(String)
    ml_confidence = Column(Float)
    ml_details = Column(JSON)  # Individual model results
    
    # News sentiment
    news_signal = Column(String)
    news_confidence = Column(Float)
    
    # Final prediction
    final_signal = Column(String, nullable=False)
    final_confidence = Column(Float, nullable=False)
    target_price = Column(Float)
    target_type = Column(String)  # HIGH or LOW
    
    # Actual outcome (for validation)
    actual_high = Column(Float)
    actual_low = Column(Float)
    outcome_verified_at = Column(DateTime)


# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
