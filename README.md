# AI Market Analysis Assistant

An AI-powered stock market analysis platform for Indian markets (NSE/BSE) that provides real-time sentiment analysis, news aggregation, and AI-generated insights using OpenAI and RAG (Retrieval-Augmented Generation).

## Features

- 📊 **Real-Time Stock Data**: Live price data for NSE and BSE stocks
- 🤖 **AI-Powered Analysis**: RAG-based insights combining market news with OpenAI's LLM
- 📰 **News Aggregation**: Automated scraping from MoneyControl and Economic Times
- 💭 **Sentiment Analysis**: AI-driven sentiment scoring with bullish/bearish classification
- 🛡️ **Compliance Guardrails**: Built-in validation to ensure information-only outputs
- 🔍 **Vector Search**: ChromaDB-powered semantic search for relevant news
- 🎨 **Modern UI**: Beautiful Next.js dashboard with TailwindCSS

## Architecture

```
Backend (FastAPI + Python)
├── Data Ingestion
│   ├── Yahoo Finance API (real-time stock data)
│   ├── Web Scrapers (MoneyControl, Economic Times)
│   └── Data Normalization Pipeline
├── AI Services
│   ├── OpenAI Embeddings (text-embedding-3-large)
│   ├── ChromaDB Vector Database
│   ├── Sentiment Analysis (OpenAI GPT-4o-mini)
│   ├── RAG Service (retrieval + generation)
│   └── Guardrails (compliance validation)
└── REST API
    ├── Authentication (JWT tokens)
    ├── Stock Endpoints
    ├── Sentiment Analysis
    └── News Feed

Frontend (Next.js + TypeScript)
├── Landing Page
├── Authentication (Login/Signup)
├── Dashboard
└── Stock Detail Pages

Infrastructure
├── MySQL (user data, preferences)
├── ChromaDB (vector embeddings)
└── Docker Compose (orchestration)
```

## Tech Stack

### Backend
- **FastAPI**: Web framework
- **OpenAI**: Embeddings & LLM (GPT-4o-mini)
- **ChromaDB**: Vector database
- **spaCy**: NER for ticker extraction
- **BeautifulSoup**: Web scraping
- **MySQL**: Relational database
- **SQLAlchemy**: ORM

### Frontend
- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **TailwindCSS**: Styling
- **Axios**: API client

## Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- 8GB+ RAM (for models and vector DB)

## Quick Start

### 1. Clone and Setup

```bash
cd /Volumes/AshDrive/prjts/stockmarket
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your keys:
# - OPENAI_API_KEY (required)
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
nano .env
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up --build
```

This will start:
- **MySQL** on port 3306
- **Backend API** on port 8000
- **Frontend** on port 3000

### 4. Initialize Data

```bash
# Run initial data ingestion (in a new terminal)
curl -X POST http://localhost:8000/admin/ingest
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

### 1. Create Account
- Navigate to http://localhost:3000
- Click "Sign Up"
- Create an account

### 2. Search Stocks
- Use the search bar to find defense stocks (HAL, BEL, BDL, MDL, etc.)
- Click on a stock to view detailed analysis

### 3. View Analysis
- Real-time price data
- AI-generated sentiment analysis
- Key insights and risk factors
- News references

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login

### Stocks
- `GET /stocks/search?q={query}` - Search stocks
- `GET /stocks/{ticker}/data` - Real-time stock data
- `GET /stocks/{ticker}/analysis` - AI analysis

### Sentiment
- `GET /sentiment/{ticker}` - Ticker sentiment
- `GET /sentiment/sector/{sector}` - Sector sentiment

### News
- `GET /news/feed` - News feed
- `GET /news/{ticker}` - Ticker-specific news

### Admin
- `POST /admin/ingest` - Trigger data ingestion

## Data Sources

1. **Stock Data**: Yahoo Finance (via Python yfinance)
2. **News Articles**:
   - MoneyControl (web scraping)
   - Economic Times (web scraping)

## Configuration

### Backend Environment Variables
```env
# Required
OPENAI_API_KEY=your_key_here
JWT_SECRET_KEY=your_secret_here

# Database (configured in docker-compose.yml)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=stockmarket_user
MYSQL_PASSWORD=secure_password_123
MYSQL_DATABASE=stockmarket_db

# Paths
DATA_DIR=/app/data
CHROMA_DB_PATH=/app/data/chroma_db

# AI Models
EMBEDDING_MODEL=text-embedding-3-large
SENTIMENT_MODEL=gpt-4o-mini
```

## Development

### Run Backend Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set environment variables
export OPENAI_API_KEY=your_key
export MYSQL_HOST=localhost
# ... other variables

# Run server
uvicorn app.main:app --reload --port 8000
```

### Run Frontend Locally

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Compliance & Guardrails

The system includes built-in guardrails to ensure all outputs are:
- ✅ Informational only (never financial advice)
- ✅ Free from buy/sell recommendations
- ✅ Validated against compliance rules
- ✅ Always include disclaimers

Forbidden phrases are automatically sanitized or flagged.

## Supported Stocks (MVP)

### Defense Sector
- HAL - Hindustan Aeronautics Limited
- BEL - Bharat Electronics Limited
- BDL - Bharat Dynamics Limited
- MDL - Mazagon Dock Shipbuilders
- GRSE - Garden Reach Shipbuilders
- BEML - BEML Limited

More stocks can be added by extending the ticker list.

## Roadmap

- [ ] Add scheduled data ingestion (cron jobs)
- [ ] Implement fine-tuned DistilBERT for sentiment
- [ ] Add watchlist functionality
- [ ] Expand to more sectors
- [ ] Add historical trend analysis
- [ ] Multi-country support (US, UK markets)
- [ ] Real-time WebSocket updates

## Troubleshooting

### ChromaDB not persisting
- Ensure `/app/data/chroma_db` volume is mounted correctly
- Check write permissions on the volume

### Scraping errors
- Some websites may block automated requests
- Adjust `SCRAPER_DELAY_SECONDS` in .env
- Verify website structure hasn't changed

### OpenAI rate limits
- Use a paid OpenAI account
- Implement caching for embeddings
- Reduce batch sizes

## License

MIT

## Disclaimer

⚠️ **IMPORTANT**: This platform is for educational and informational purposes only. It does not provide financial advice. Always consult with qualified financial advisors before making investment decisions. Past performance does not guarantee future results.

## Contributing

Contributions welcome! Please open an issue or submit a PR.

## Support

For issues or questions, please open a GitHub issue.
