"""
MoltBot Trading Platform - FastAPI Backend
Main application with REST API and WebSocket support (v1.0.1)
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import json

from config import settings, COIN_DISPLAY_NAMES, DEFAULT_USER_SETTINGS
from models import init_db, get_db, UserSettings, TradeHistory
from prediction.prediction_engine import PredictionEngine
from data.market_data_collector import MarketDataCollector
from ml.model_trainer import MLModelTrainer
import structlog

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced crypto trading prediction and auto-trade platform"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Global instances
prediction_engine = None
market_collector = None


# Pydantic models for API
class PredictionRequest(BaseModel):
    coin: str
    timeframe: str
    min_confidence: Optional[int] = 60


class UserSettingsUpdate(BaseModel):
    mode: Optional[str] = None
    coin: Optional[str] = None
    timeframe: Optional[str] = None
    confidence_threshold: Optional[int] = None
    visible_sections: Optional[Dict] = None
    enabled_strategies: Optional[Dict] = None


# ----------------------------------------
# STARTUP & HEALTH
# ----------------------------------------

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global prediction_engine
    
    logger.info("Starting MoltBot backend...")
    
    # Initialize global instances
    market_collector = MarketDataCollector()
    prediction_engine = PredictionEngine()
    
    logger.info("MoltBot backend started successfully")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "prediction_engine": "initialized" if prediction_engine else "not initialized"
    }


# ----------------------------------------
# COIN & CONFIG ENDPOINTS
# ----------------------------------------

@app.get("/api/coins")
async def get_supported_coins():
    """Get list of supported coins"""
    coins = [
        {
            "symbol": coin,
            "name": COIN_DISPLAY_NAMES.get(coin, coin),
            "pair": f"{coin}/USDT"
        }
        for coin in settings.SUPPORTED_COINS
    ]
    return {"coins": coins}


@app.get("/api/timeframes")
async def get_timeframes():
    """Get available timeframes"""
    return {"timeframes": settings.TIMEFRAMES}


@app.get("/api/config")
async def get_config():
    """Get system configuration"""
    return {
        "weights": {
            "strategy": settings.STRATEGY_WEIGHT,
            "ml": settings.ML_WEIGHT,
            "news": settings.NEWS_WEIGHT
        },
        "thresholds": {
            "min_confidence": settings.MIN_CONFIDENCE_THRESHOLD,
            "high_confidence": settings.HIGH_CONFIDENCE_THRESHOLD
        },
        "risk": {
            "max_trade_risk": settings.MAX_TRADE_RISK_PERCENT,
            "stop_loss": settings.DEFAULT_STOP_LOSS_PERCENT,
            "take_profit": settings.DEFAULT_TAKE_PROFIT_PERCENT
        }
    }


# ----------------------------------------
# MARKET DATA ENDPOINTS
# ----------------------------------------

@app.get("/api/market-data/{coin}/{timeframe}")
async def get_market_data(coin: str, timeframe: str, limit: int = 100, include_indicators: bool = True):
    """
    Get OHLCV market data for a coin
    
    Args:
        coin: Coin symbol (BTC, ETH, etc.)
        timeframe: Timeframe (1s, 1m, 1h, etc.)
        limit: Number of candles (default 100)
        include_indicators: Whether to include technical indicators
    """
    if coin not in settings.SUPPORTED_COINS:
        raise HTTPException(status_code=400, detail=f"Unsupported coin: {coin}")
    
    if timeframe not in settings.TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {timeframe}")
    
    try:
        global market_collector
        if not market_collector:
            market_collector = MarketDataCollector()
            
        df = market_collector.get_ohlcv(coin, timeframe, limit=limit)
        
        if df is None:
            raise HTTPException(status_code=500, detail="Failed to fetch market data")
        
        if include_indicators:
            from data.historical_loader import HistoricalDataLoader
            loader = HistoricalDataLoader()
            df = loader.add_technical_indicators(df)
        
        # Convert DataFrame to list of dicts
        data = df.to_dict('records')
        
        # Use prediction_engine's serialization helper
        if prediction_engine:
            data = prediction_engine._clean_for_serialization(data)
        
        return {
            "coin": coin,
            "timeframe": timeframe,
            "data": data,
            "count": len(data)
        }
    
    except Exception as e:
        logger.error("Error fetching market data", coin=coin, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/current-price/{coin}")
async def get_current_price(coin: str):
    """Get current price for a coin"""
    if coin not in settings.SUPPORTED_COINS:
        raise HTTPException(status_code=400, detail=f"Unsupported coin: {coin}")
    
    try:
        collector = MarketDataCollector()
        price = collector.get_current_price(coin)
        
        if price is None:
            raise HTTPException(status_code=500, detail="Failed to fetch price")
        
        return {
            "coin": coin,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error("Error fetching price", coin=coin, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# PREDICTION ENDPOINTS
# ----------------------------------------

@app.post("/api/prediction")
async def create_prediction(request: PredictionRequest):
    """
    Generate prediction for a coin/timeframe
    
    Args:
        request: Prediction request with coin, timeframe, min_confidence
    """
    if request.coin not in settings.SUPPORTED_COINS:
        raise HTTPException(status_code=400, detail=f"Unsupported coin: {request.coin}")
    
    if request.timeframe not in settings.TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {request.timeframe}")
    
    try:
        if prediction_engine is None:
            raise HTTPException(status_code=500, detail="Prediction engine not initialized")
        
        prediction = prediction_engine.predict(
            request.coin,
            request.timeframe,
            request.min_confidence
        )
        
        # DEBUG LOGGING
        logger.info("Prediction generated", type=str(type(prediction)))
        if isinstance(prediction, dict):
             logger.info("Prediction keys", keys=list(prediction.keys()))
        
        return prediction
    
    except Exception as e:
        logger.error("Error generating prediction", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prediction/{coin}/{timeframe}")
async def get_prediction(coin: str, timeframe: str, min_confidence: int = 60):
    """Get prediction for a coin/timeframe (GET version)"""
    request = PredictionRequest(coin=coin, timeframe=timeframe, min_confidence=min_confidence)
    return await create_prediction(request)


# ----------------------------------------
# USER SETTINGS ENDPOINTS
# ----------------------------------------

@app.get("/api/settings")
async def get_user_settings(db=Depends(get_db)):
    """Get user settings"""
    try:
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == "default").first()
        
        if not settings_obj:
            # Create default settings
            settings_obj = UserSettings(
                user_id="default",
                **DEFAULT_USER_SETTINGS
            )
            db.add(settings_obj)
            db.commit()
            db.refresh(settings_obj)
        
        return {
            "mode": settings_obj.mode,
            "coin": settings_obj.coin,
            "timeframe": settings_obj.timeframe,
            "confidence_threshold": settings_obj.confidence_threshold,
            "visible_sections": settings_obj.visible_sections,
            "enabled_strategies": settings_obj.enabled_strategies
        }
    
    except Exception as e:
        logger.error("Error fetching settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_user_settings(update: UserSettingsUpdate, db=Depends(get_db)):
    """Update user settings"""
    try:
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == "default").first()
        
        if not settings_obj:
            settings_obj = UserSettings(user_id="default", **DEFAULT_USER_SETTINGS)
            db.add(settings_obj)
        
        # Update fields
        if update.mode:
            settings_obj.mode = update.mode
        if update.coin:
            settings_obj.coin = update.coin
        if update.timeframe:
            settings_obj.timeframe = update.timeframe
        if update.confidence_threshold is not None:
            settings_obj.confidence_threshold = update.confidence_threshold
        if update.visible_sections:
            settings_obj.visible_sections = update.visible_sections
        if update.enabled_strategies:
            settings_obj.enabled_strategies = update.enabled_strategies
        
        db.commit()
        db.refresh(settings_obj)
        
        return {"status": "success", "message": "Settings updated"}
    
    except Exception as e:
        logger.error("Error updating settings", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# TRADE HISTORY ENDPOINTS
# ----------------------------------------

@app.get("/api/trade-history")
async def get_trade_history(limit: int = 50, db=Depends(get_db)):
    """Get trade history"""
    try:
        trades = db.query(TradeHistory).order_by(
            TradeHistory.timestamp.desc()
        ).limit(limit).all()
        
        history = [{
            "id": t.id,
            "timestamp": t.timestamp.isoformat(),
            "coin": t.coin,
            "signal": t.signal,
            "confidence": t.confidence,
            "entry_price": t.entry_price,
            "target_price": t.target_price,
            "status": t.status,
            "profit_loss": t.profit_loss
        } for t in trades]
        
        return {"trades": history, "count": len(history)}
    
    except Exception as e:
        logger.error("Error fetching trade history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# ML TRAINING ENDPOINT
# ----------------------------------------

@app.post("/api/train-models")
async def train_models(coin: str, timeframe: str):
    """Train ML models for a coin/timeframe"""
    if coin not in settings.SUPPORTED_COINS:
        raise HTTPException(status_code=400, detail=f"Unsupported coin: {coin}")
    
    try:
        trainer = MLModelTrainer()
        results = trainer.train_all_models(coin, timeframe)
        
        if results is None:
            raise HTTPException(status_code=500, detail="Training failed")
        
        return {
            "status": "success",
            "coin": coin,
            "timeframe": timeframe,
            "models": {
                name: {"accuracy": res['accuracy']}
                for name, res in results.items()
            }
        }
    
    except Exception as e:
        logger.error("Error training models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------
# WEBSOCKET FOR REAL-TIME UPDATES
# ----------------------------------------

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", total=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected", total=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket endpoint for real-time market updates"""
    await manager.connect(websocket)
    
    current_coin = 'BTC'
    current_timeframe = '1h'
    
    # Task to listen for client messages
    async def listen_for_messages():
        nonlocal current_coin, current_timeframe
        try:
            while True:
                data = await websocket.receive_json()
                if 'coin' in data:
                    current_coin = data['coin']
                if 'timeframe' in data:
                    current_timeframe = data['timeframe']
                logger.info("WebSocket subscription updated", coin=current_coin, timeframe=current_timeframe)
                # Send immediate update on change
                await send_full_update()
        except:
            pass

    async def send_full_update():
        logger.info("Executing WebSocket full update", coin=current_coin, timeframe=current_timeframe)
        if prediction_engine:
            try:
                # 1. Get Prediction (Run in thread to avoid blocking loop)
                prediction = await asyncio.to_thread(prediction_engine.predict, current_coin, current_timeframe)
                
                # 2. Get Market Data (Run in thread to avoid blocking loop)
                def fetch_data():
                    global market_collector
                    if not market_collector:
                        market_collector = MarketDataCollector()
                        
                    df = market_collector.get_ohlcv(current_coin, current_timeframe, limit=100)
                    if df is not None:
                        from data.historical_loader import HistoricalDataLoader
                        loader = HistoricalDataLoader()
                        df = loader.add_technical_indicators(df)
                        market_data = df.to_dict('records')
                        
                        # Clean for serialization
                        if prediction_engine:
                            market_data = prediction_engine._clean_for_serialization(market_data)
                        return market_data
                    return None

                market_data = await asyncio.to_thread(fetch_data)
                
                if market_data:
                    # Clean prediction for serialization
                    if prediction_engine:
                        prediction = prediction_engine._clean_for_serialization(prediction)
                        
                    combined_payload = {
                        "type": "full_update",
                        "coin": current_coin,
                        "timeframe": current_timeframe,
                        "prediction": prediction,
                        "market_data": market_data
                    }
                    # Force serialization of any remaining complex types (like Timestamps)
                    import json
                    json_payload = json.dumps(combined_payload, default=str)
                    await websocket.send_text(json_payload)
            except Exception as e:
                import traceback
                logger.error("Error in WebSocket update", error=str(e), traceback=traceback.format_exc())

    # Start listener task
    listener_task = asyncio.create_task(listen_for_messages())
    
    try:
        # Initial update
        await send_full_update()
        
        while True:
            # Send periodical update every 10 seconds
            await asyncio.sleep(10)
            await send_full_update()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(websocket)
    finally:
        listener_task.cancel()


# ----------------------------------------
# RUN SERVER
# ----------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
