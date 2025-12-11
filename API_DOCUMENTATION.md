# API Documentation & Usage Guide

## Quick Start Commands

### 1. Start the Application

```bash
# Start all services (Backend, MySQL, Frontend)
docker-compose up -d

# Check status
docker-compose ps

# View backend logs
docker logs -f stockmarket_backend

# View Streamlit output
docker logs -f stockmarket_backend --tail 100 | grep streamlit
```

### 2. Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean restart)
docker-compose down -v
```

### 3. Access Points

- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **Frontend (Next.js)**: http://localhost:3000

---

## API Endpoints & cURL Commands

### Authentication

#### Sign Up
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com"
}
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

---

### Stocks API

#### Search Stocks
```bash
# Search for HAL
curl -X GET "http://localhost:8000/stocks/search?query=HAL"

# Search for Indian stocks
curl -X GET "http://localhost:8000/stocks/search?query=Reliance"
```

**Response:**
```json
{
  "results": [
    {
      "ticker": "HAL",
      "name": "Hindustan Aeronautics Limited",
      "exchange": "NSE"
    }
  ]
}
```

#### Get Stock Data
```bash
# Get current stock data
curl -X GET http://localhost:8000/stocks/HAL/data

# Get data from specific provider
curl -X GET "http://localhost:8000/stocks/HAL/data?provider=Finnhub"
curl -X GET "http://localhost:8000/stocks/HAL/data?provider=Alpha%20Vantage"
curl -X GET "http://localhost:8000/stocks/HAL/data?provider=Yahoo%20Finance"
```

**Response:**
```json
{
  "ticker": "HAL",
  "exchange": "NSE",
  "current_price": 4250.50,
  "previous_close": 4200.00,
  "day_high": 4300.00,
  "day_low": 4180.00,
  "volume": 1500000,
  "currency": "INR",
  "timestamp": "2025-12-04T10:15:00",
  "provider": "Finnhub"
}
```

#### Get Stock Analysis (RAG-powered)
```bash
# Get AI-powered analysis
curl -X GET http://localhost:8000/stocks/HAL/analysis

# This triggers:
# 1. News scraping (DuckDuckGo + Google RSS)
# 2. Sentiment analysis
# 3. RAG-based prediction
# 4. Caching for 1 hour
```

**Response:**
```json
{
  "ticker": "HAL",
  "analysis": "Hindustan Aeronautics shows strong fundamentals...",
  "reasoning": "Key drivers include defense contracts...",
  "prediction": "The outlook suggests potential upside if...",
  "risk_factors": [
    "Dependency on government contracts",
    "Execution delays in projects"
  ],
  "sentiment": {
    "classification": "bullish",
    "aggregate_score": 0.65,
    "confidence": 0.78
  },
  "references": [
    {
      "source": "Economic Times",
      "url": "https://...",
      "timestamp": "2025-12-04"
    }
  ],
  "key_insights": [
    "Recent contract wins boost revenue visibility",
    "Strong order book provides stability"
  ],
  "current_price": 4250.50,
  "cached": false
}
```

#### Get Stock Operation Logs
```bash
curl -X GET http://localhost:8000/stocks/HAL/logs
```

---

### News API

#### Get General News Feed
```bash
curl -X GET http://localhost:8000/news/feed
```

#### Get News by Ticker
```bash
curl -X GET http://localhost:8000/news/HAL
```

**Response:**
```json
{
  "ticker": "HAL",
  "articles": [
    {
      "title": "HAL wins defense contract",
      "url": "https://...",
      "source": "Economic Times",
      "timestamp": "2025-12-04",
      "sentiment": "bullish"
    }
  ]
}
```

---

### Admin API

#### Trigger Manual Ingestion
```bash
# Force scrape all sources
curl -X POST http://localhost:8000/admin/ingest
```

**Response:**
```json
{
  "status": "success",
  "message": "Data ingestion completed",
  "report": {
    "duration_seconds": 45.2,
    "total_articles": 150,
    "sources": [
      {
        "source": "DuckDuckGo News",
        "success": true,
        "articles_count": 100
      }
    ]
  }
}
```

#### Get System Status
```bash
curl -X GET http://localhost:8000/admin/status
```

**Response:**
```json
{
  "scrapers": [
    {
      "source_name": "Google News RSS",
      "health_status": "healthy",
      "success_rate": 100.0,
      "last_success": "2025-12-04T10:00:00"
    },
    {
      "source_name": "DuckDuckGo News",
      "health_status": "healthy",
      "success_rate": 100.0
    }
  ],
  "apis": [
    {
      "source_name": "Finnhub",
      "health_status": "healthy",
      "success_rate": 98.5
    }
  ]
}
```

#### Get Recent Errors
```bash
curl -X GET "http://localhost:8000/admin/errors?limit=10"
```

#### Get Operation Logs
```bash
curl -X GET "http://localhost:8000/admin/logs?limit=50"
```

#### Get Statistics
```bash
curl -X GET http://localhost:8000/admin/stats
```

**Response:**
```json
{
  "last_24h": {
    "total_operations": 350,
    "successful_operations": 340,
    "failed_operations": 10,
    "total_articles": 1500,
    "total_chunks": 4500
  },
  "all_time": {
    "total_operations": 5000,
    "success_rate": 97.5
  }
}
```

#### Get Source Details
```bash
curl -X GET "http://localhost:8000/admin/sources/DuckDuckGo%20News"
```

#### Clear Old Logs
```bash
# Delete logs older than 7 days
curl -X DELETE "http://localhost:8000/admin/logs?days=7"
```

---

### Sentiment API

#### Get Sentiment by Ticker
```bash
curl -X GET http://localhost:8000/sentiment/HAL
```

**Response:**
```json
{
  "ticker": "HAL",
  "sentiment": {
    "classification": "bullish",
    "score": 0.65,
    "confidence": 0.78
  },
  "article_sentiments": [
    {
      "title": "...",
      "sentiment": "bullish",
      "score": 0.7
    }
  ]
}
```

#### Get Sector Sentiment
```bash
curl -X GET http://localhost:8000/sentiment/sector/technology
```

---

## Development Commands

### Backend Container

```bash
# Access backend shell
docker exec -it stockmarket_backend bash

# Run Python script
docker exec stockmarket_backend python /app/app/script.py

# Install package
docker exec stockmarket_backend pip install package-name

# View environment variables
docker exec stockmarket_backend env | grep AZURE
```

### Database

```bash
# Access MySQL
docker exec -it stockmarket_mysql mysql -u stockmarket_user -p
# Password: secure_password_123

# Show databases
docker exec stockmarket_mysql mysql -u stockmarket_user -psecure_password_123 -e "SHOW DATABASES;"

# Query operation logs
docker exec stockmarket_mysql mysql -u stockmarket_user -psecure_password_123 stockmarket_db -e "SELECT * FROM operation_logs ORDER BY timestamp DESC LIMIT 10;"
```

### Logs & Debugging

```bash
# Follow all logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# MySQL only
docker-compose logs -f mysql

# Check ChromaDB status
docker exec stockmarket_backend ls -la /app/data/chroma_db/
```

---

## Testing Workflow

### 1. Complete Analysis Flow
```bash
# Step 1: Search for stock
curl -X GET "http://localhost:8000/stocks/search?query=HAL"

# Step 2: Get current price
curl -X GET http://localhost:8000/stocks/HAL/data

# Step 3: Get AI analysis (triggers scraping)
curl -X GET http://localhost:8000/stocks/HAL/analysis

# Step 4: Get same analysis (cached - instant)
curl -X GET http://localhost:8000/stocks/HAL/analysis

# Step 5: Check system status
curl -X GET http://localhost:8000/admin/status
```

### 2. Test API Providers
```bash
# Test each provider
for provider in "Finnhub" "Alpha Vantage" "Yahoo Finance" "Marketstack"; do
  echo "Testing $provider..."
  curl -X GET "http://localhost:8000/stocks/HAL/data?provider=$provider"
  echo ""
done
```

### 3. Monitor Scraping
```bash
# Trigger ingestion
curl -X POST http://localhost:8000/admin/ingest

# Watch logs
docker logs -f stockmarket_backend | grep "scrape"
```

---

## Postman Collection

Import `StockMarket_API.postman_collection.json` into Postman:

1. Open Postman
2. Click **Import**
3. Select the JSON file
4. Set `base_url` variable to `http://localhost:8000`
5. Test all endpoints

---

## Environment Variables

Required in `.env` file:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Stock APIs
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
MARKETSTACK_API_KEY=your_key

# Database
MYSQL_PASSWORD=secure_password_123

# JWT
JWT_SECRET_KEY=your-secret-key-change-this
```

---

## Troubleshooting

### Backend not responding
```bash
# Restart backend
docker-compose restart backend

# Check backend is running
docker ps | grep backend

# View recent logs
docker logs --tail 50 stockmarket_backend
```

### Database connection issues
```bash
# Check MySQL is running
docker ps | grep mysql

# Test connection
docker exec stockmarket_backend python -c "from app.core.database import get_db; print('DB OK')"
```

### Scraper not working
```bash
# Check sources configuration
docker exec stockmarket_backend cat /app/config/sources.yaml

# Test DuckDuckGo scraper
docker exec stockmarket_backend python /app/test_ddg.py
```
