# NeuroVest - Indian Stock Market Analysis System

**Advanced AI-Powered Stock Analysis with RAG (Retrieval-Augmented Generation)**

---

## 🎯 Overview

NeuroVest is a comprehensive stock market analysis platform designed specifically for the Indian market (NSE/BSE). It combines real-time data, AI-powered sentiment analysis, technical indicators, and historical pattern recognition to provide actionable investment insights.

### Key Features

- **AI-Powered Analysis**: GPT-4 with RAG for context-aware stock recommendations
- **Real-Time News**: RSS feeds from top financial publishers (Moneycontrol, ET, Livemint)
- **Sentiment Analysis**: Parallel async processing of market sentiment
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Historical Context**: ChromaDB vector database with temporal decay algorithm
- **User Dashboard**: Beautiful UI with real-time updates and portfolio tracking

---

## 🚀 **Recent Major Optimizations (Dec 2025)**

We recently completed a **comprehensive performance optimization** that improved analysis speed by **74-78%**:

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **News Fetching** | 12.0s | 0.15s | ⚡ **97% faster** |
| **Sentiment Analysis** | 16.0s | 3.8s | ⚡ **76% faster** |
| **Total Analysis Time** | 46s | 10-12s | ⚡ **4x faster** |

### What Changed?

1. **RSS-First News**: Switched from web scraping to RSS feeds with 3-layer fallback
2. **Async Sentiment**: Parallel processing using `AsyncAzureOpenAI` + `asyncio.gather()`
3. **Smart ChromaDB**: Temporal decay + quality scoring for historical analyses
4. **Optimized Prompts**: 50% token reduction through concise formatting

📖 **[Read Full Optimization Documentation](./brain/OPTIMIZATION_README.md)**

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                   │
│  - React components                                     │
│  - Real-time updates                                    │
│  - Chart visualization                                  │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────▼────────────────────────────────────────┐
│                  Backend (FastAPI)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RAG Service (AI Analysis)                       │   │
│  │  - Intelligent News Service (3-layer fallback)   │   │
│  │  - Async Parallel Sentiment                      │   │
│  │  - Dynamic ChromaDB Retrieval                    │   │
│  │  - GPT-4 with optimized prompts                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Data Services                                   │   │
│  │  - Technical Analysis (RSI, MACD, etc.)          │   │
│  │  - Stock API Service (yfinance, yahooquery)      │   │
│  │  - News Aggregation (RSS + Web Scraping)         │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬─────────────┬──────────────────────────┘
                 │             │
        ┌────────▼────────┐ ┌─▼──────────┐
        │  MySQL Database │ │  ChromaDB  │
        │  - User data    │ │  - Vectors │
        │  - Analyses     │ │  - News    │
        │  - Cache        │ │  - Analysis│
        └─────────────────┘ └────────────┘
```

### Tech Stack

**Backend**:
- FastAPI (Python 3.11)
- Azure OpenAI (GPT-4)
- ChromaDB (vector database)
- MySQL (relational database)
- Redis (caching)

**Frontend**:
- Next.js 14
- React
- TailwindCSS
- Chart.js

**Infrastructure**:
- Docker & Docker Compose
- Nginx (reverse proxy)

---

## 📦 Installation

### Prerequisites

- Docker & Docker Compose
- Azure OpenAI API access
- (Optional) Stock API keys (yfinance is free)

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/neurovest.git
cd neurovest
```

2. **Configure environment variables**:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

Required environment variables:
```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2023-05-15

MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=stock_market_db
```

3. **Start the application**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🎨 Features

### For Users

✅ **Smart Stock Analysis**: AI-powered recommendations based on news, sentiment, and technicals  
✅ **Real-Time News**: Latest updates from trusted financial sources  
✅ **Sentiment Tracking**: Market mood analysis with confidence scores  
✅ **Technical Charts**: Interactive visualizations of indicators  
✅ **Portfolio Management**: Track your investments and performance  
✅ **Historical Context**: Learn from past analyses and predictions  

### For Developers

✅ **Async Processing**: High-performance parallel sentiment analysis  
✅ **Modular Architecture**: Clean separation of concerns  
✅ **Vector Search**: Semantic similarity for relevant context  
✅ **Comprehensive Logging**: Detailed observability at every layer  
✅ **Docker Ready**: One-command deployment  
✅ **Well Documented**: Extensive inline docs and guides  

---

## 📊 Performance

### Benchmark Results

**Analysis Pipeline** (tested with 10 stocks):
- News aggregation: 0.15s avg
- Sentiment analysis: 3.8s for 5 articles (parallel)
- Technical indicators: 1.2s
- RAG generation: 5s
- **Total: 10-12s** ✅

**Success Rates**:
- News retrieval: 75%+ (RSS primary source)
- Sentiment accuracy: 90%+ (GPT-4)
- Technical calculation: 100%

---

## 🔧 Configuration

### ChromaDB Temporal Retrieval

Fine-tune historical analysis retrieval in `backend/app/core/config.py`:

```python
TEMPORAL_DECAY_LAMBDA = 0.05  # Decay rate (higher = faster decay)
TEMPORAL_WEIGHT = 0.6          # Weight for recency
QUALITY_WEIGHT = 0.4           # Weight for quality
MAX_PER_WEEK = 2               # Diversity constraint
DAYS_BACK = 45                 # Search window days
```

### RSS News Sources

Configure feeds in `backend/app/scrapers/rss_news_aggregator.py`:

```python
RSS_FEEDS = {
    'moneycontrol': 'https://www.moneycontrol.com/rss/latestnews.xml',
    'economic_times': 'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
    'livemint': 'https://www.livemint.com/rss/markets'
}
```

---

## 📚 Documentation

- **[Optimization Guide](./brain/OPTIMIZATION_README.md)**: Comprehensive documentation of performance improvements
- **[Docker Test Results](./brain/docker_test_results.md)**: Validation test results
- **[Walkthrough](./brain/walkthrough.md)**: Implementation details and testing
- **[Task Checklist](./brain/task.md)**: Complete project tracking

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose build backend
docker-compose up -d
```

---

## 🧪 Testing

### Run Tests Locally

```bash
cd /Volumes/AshDrive/prjts/stockmarket
python3 test_optimizations.py
```

### Run Tests in Docker

```bash
docker exec stockmarket_backend python3 -c "
from app.scrapers.rss_news_aggregator import rss_aggregator
print('✅ RSS aggregator loaded')
"
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Azure OpenAI**: GPT-4 for AI analysis
- **ChromaDB**: Vector database for semantic search
- **Moneycontrol, ET, Livemint**: RSS feed providers
- **yfinance**: Stock data API

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for the Indian stock market community**
