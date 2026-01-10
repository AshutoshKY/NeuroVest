# System Architecture

## Overview

NeuroVest is a hybrid AI stock analysis platform combining technical indicators with Large Language Models (LLM).

## Core Components

1.  **Backend (FastAPI)**
    *   **Signal Engine**: Generates technical signals (RSI, MACD, Trends).
    *   **RAG Engine**: Retrieves news and historical context.
    *   **LLM Integration**: Azure OpenAI (GPT-4) for narrative analysis.
    *   **Smart Orchestrator**: Manages API calls and failover.

2.  **Frontend (Next.js)**
    *   **Dashboard**: Real-time stock view.
    *   **Analysis View**: Deep dive into specific tickers.

3.  **Infrastructure**
    *   **Database**: MySQL (User data, Signal history).
    *   **Vector DB**: ChromaDB (News embeddings).
    *   **Cache**: Redis (Rate limiting, API response caching).
