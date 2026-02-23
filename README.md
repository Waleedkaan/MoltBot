# TradeBot - Advanced Crypto Trading Platform

TradeBot is a full-featured crypto trading prediction and optional auto-trade system with multi-strategy analysis, machine learning models, sentiment analysis, and real-time visualization.

![MoltBot](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

 ✨ Features

 📊 **Multi-Strategy Analysis**
- **RSI Strategy**: Overbought/oversold detection
- **EMA Crossover**: Golden/death cross signals  
- **MACD**: Momentum-based signals
- **Bollinger Bands**: Volatility breakout detection
- **Volume Spike**: Unusual volume + price direction
- **Support/Resistance**: Dynamic S/R level detection

 🤖 **Machine Learning Models**
- Logistic Regression
- Random Forest
- XGBoost
- LSTM (TensorFlow/PyTorch)
- Walk-forward validation
- Ensemble voting

 📰 **News & Sentiment Analysis**
- CryptoPanic RSS feed integration
- Fear & Greed Index
- NLP sentiment scoring
- Aggregated confidence

 🎯 **Smart Predictions**
- Weighted signal combination (Strategy 40%, ML 35%, News 25%)
- Dynamic target price calculation using ATR
- **BUY signal** → Predicted HIGH price
- **SELL signal** → Predicted LOW price
- Confidence-based threshold filtering

 💎 **Professional UI**
- Real-time candlestick charts (Lightweight Charts)
- Glassmorphism design with Tailwind CSS
- Live signal cards with confidence bars
- Interactive visibility toggles
- Responsive mobile-first layout

 🔐 **User Control**
- **Prediction-only mode** (default) - No trades executed
- **Auto-trade mode** (optional) - Requires API keys
- Toggle individual strategies
- Timeframe selection: 15m, 1h, 4h, 1D
- 20 supported coins

---

 🛠️ Tech Stack

 Backend
- **Framework**: FastAPI
- **Data Sources**: Binance Public API, Yahoo Finance
- **Indicators**: pandas-ta, TA-Lib
- **ML**: scikit-learn, XGBoost, TensorFlow, PyTorch
- **Sentiment**: transformers, TextBlob
- **Database**: SQLite
- **Exchange**: CCXT (for auto-trade)

 Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Charts**: Lightweight Charts
- **State**: React Query
- **HTTP**: Axios

---

 📦 Installation

### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **pip** and **npm**

 1. Clone Repository
```bash
git clone <repository-url>
cd "Trading Bot"
```

 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env

# Edit .env with your settings (optional)
# For prediction-only mode, no API keys needed
```

 3. Initialize Database
```bash
python -c "from models import init_db; init_db()"
```

 4. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install
```

---

 🚀 Running the Application

 Start Backend (Terminal 1)
```bash
cd backend
python main.py
```
Backend will run on `http://localhost:8000`

 Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Frontend will run on `http://localhost:3000`

 Access Application
Open your browser and navigate to:
```
http://localhost:3000
```

---

 📚 API Documentation

Once the backend is running, access the interactive API docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

 Key Endpoints

```
GET  /api/coins                 - List supported coins
GET  /api/timeframes            - List timeframes
GET  /api/market-data/{coin}/{timeframe}  - OHLCV data
GET  /api/prediction/{coin}/{timeframe}   - Get prediction
POST /api/settings              - Update user settings
GET  /api/trade-history         - Trade history (if auto-trade)
POST /api/train-models          - Train ML models
```

---

  Configuration

 Environment Variables (`.env`)

```env
# Risk Management
MAX_TRADE_RISK_PERCENT=2.0
DEFAULT_STOP_LOSS_PERCENT=3.0
DEFAULT_TAKE_PROFIT_PERCENT=5.0

# Confidence Thresholds
MIN_CONFIDENCE_THRESHOLD=60
HIGH_CONFIDENCE_THRESHOLD=75

# Prediction Weights
STRATEGY_WEIGHT=0.40
ML_WEIGHT=0.35
NEWS_WEIGHT=0.25

# Exchange API Keys (Optional - for auto-trade only)
BINANCE_API_KEY=
BINANCE_API_SECRET=
```

 Supported Coins (20 Major Cryptocurrencies)
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, TRX, MATIC, LTC, LINK, UNI, ATOM, NEAR, ICP, FIL, APT, ARB

---

 🎓 How It Works

 1. Data Collection
- Real-time OHLCV from Binance Public API
- Historical data for ML training (6 months)
- News sentiment from CryptoPanic + Fear & Greed Index

 2. Strategy Analysis
Each strategy analyzes price action and returns:
- Signal: BUY / SELL / NEUTRAL
- Confidence: 0-100%

 3. ML Prediction
Trained models predict price direction:
- Features: RSI, MACD, EMA, Volume, ATR, etc.
- Output: BUY/SELL + confidence

 4. Signal Combination
Weighted combination of all sources:
```
Final Confidence = (Strategy × 40%) + (ML × 35%) + (News × 25%)
```

 5. Target Price Calculation
```
If BUY:  Target = Current Price + (ATR × Confidence Factor)
If SELL: Target = Current Price - (ATR × Confidence Factor)
```

 6. Decision
- **Confidence ≥ 60%**: Show signal + target price
- **Confidence < 60%**: NO TRADE (low confidence)

---

 🧪 Training ML Models

Before first use, train ML models for your desired coin/timeframe:

```bash
# Via API
curl -X POST "http://localhost:8000/api/train-models?coin=BTC&timeframe=1h"

# Or via Python script
cd backend
python -c "from ml.model_trainer import MLModelTrainer; trainer = MLModelTrainer(); trainer.train_all_models('BTC', '1h')"
```

Models are saved in `backend/models/` directory.

---

 ⚠️ Safety & Legal

 ⚠️ **IMPORTANT DISCLAIMERS**

1. **No Guarantees**: Predictions are probability-based and not guaranteed
2. **Risk Warning**: Crypto trading involves significant financial risk
3. **DYOR**: Always do your own research
4. **Never Over-invest**: Only invest what you can afford to lose
5. **Not Financial Advice**: This is an educational/research tool

 Default Mode: **Prediction Only**
- No trades are executed
- No exchange API keys required
- Safe for analysis and learning

 Auto-Trade Mode (Optional)
- Requires explicit user opt-in
- Requires exchange API keys
- Implements stop-loss and position sizing
- Use at your own risk

---

 🛡️ Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use API keys with trading restrictions** (Binance: enable "Spot & Margin Trading" only, restrict IPs)
3. **Start with small amounts** when testing auto-trade
4. **Monitor trades closely** in auto-trade mode
5. **Keep software updated**

---

 📁 Project Structure

```
Trading Bot/
├── backend/
│   ├── data/              # Data collection modules
│   ├── strategies/        # Trading strategies
│   ├── ml/                # Machine learning models
│   ├── prediction/        # Prediction engine
│   ├── models.py          # Database models
│   ├── config.py          # Configuration
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   ├── App.jsx        # Main application
│   │   └── main.jsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
│
└── README.md
```

---

 🔧 Troubleshooting

 Backend Won't Start
- Check Python version: `python --version` (should be 3.9+)
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is not in use

 Frontend Won't Start
- Check Node version: `node --version` (should be 18+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check port 3000 is not in use

 No Predictions Showing
- Ensure backend is running
- Check browser console for errors
- Verify API connection in Network tab
- Try training models first

 Chart Not Displaying
- Check for JavaScript errors in console
- Ensure market data is loading (Network tab)
- Try different coin/timeframe

---

 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

 📜 License

MIT License - See LICENSE file for details

---
 🙏 Acknowledgments

- **Binance** for free public API
- **CryptoPanic** for news aggregation
- **Fear & Greed Index** by Alternative.me
- **TradingView** for charting inspiration
- **Open Source Community** for amazing libraries

---

 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing issues first

---

 🎯 Roadmap

- [ ] Add more ML models (Neural Networks, RNN)
- [ ] Implement backtesting module
- [ ] Add portfolio management
- [ ] Multi-exchange support
- [ ] Mobile app (React Native)
- [ ] Telegram bot integration
- [ ] Advanced risk management
- [ ] Paper trading mode

---

Happy Trading! 🚀📈**

*Remember: Trade responsibly and never invest more than you can afford to lose.*
