import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json

# Page config
st.set_page_config(
    page_title="Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .error-badge {
        background: #dc3545;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .warning-badge {
        background: #ffc107;
        color: black;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📈 AI Stock Market Analysis Assistant</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Stock selection
    st.sidebar.subheader("Stock Search")
    
    # Country Filter
    search_country = st.sidebar.selectbox(
        "Select Region",
        [
            "All",
            "India", 
            "United States", 
            "United Kingdom",
            "Canada",
            "Germany",
            "France",
            "China",
            "Japan",
            "Australia",
            "Brazil"
        ],
        index=1 # Default to India
    )
    
    # Define search function for streamlit-searchbox
    def search_stocks_remote(searchterm: str):
        if not searchterm:
            return []
        try:
            url = f"{API_URL}/stocks/search"
            response = requests.get(
                url, 
                params={"q": searchterm, "country": search_country}, 
                timeout=5
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                return [
                    (f"{r['ticker']} - {r['name']} ({r['exchange']})", r['ticker'])
                    for r in results
                ]
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []

    from streamlit_searchbox import st_searchbox
    
    # Check for trending selection to set default
    default_search_val = st.session_state.pop('trending_selected_ticker', None)
    
    # Use the searchbox
    selected_ticker = st_searchbox(
        search_stocks_remote,
        key="stock_search",
        label="Search for a stock...",
        placeholder="Type to search (e.g., Apple, Reliance)...",
        clear_on_submit=False,
        default=default_search_val,
        default_searchterm=default_search_val if default_search_val else ""
    )
    
    if not selected_ticker:
        st.sidebar.info("Enter a stock name to begin.")
    
    st.divider()
    
    # Trending Stocks
    st.subheader("🔥 Trending Stocks")
    
    try:
        trending_response = requests.get(f"{API_URL}/stocks/trending", timeout=5)
        if trending_response.status_code == 200:
            trending_data = trending_response.json()
            trending_stocks = trending_data.get('trending_stocks', [])
            
            if trending_stocks:
                st.caption("Most analyzed stocks recently")
                for stock in trending_stocks[:5]:
                    ticker = stock.get('ticker')
                    count = stock.get('analysis_count', 0)
                    rank = stock.get('rank', 0)
                    
                    if st.button(f"#{rank} {ticker} (×{count} analyses)", key=f"trend_{ticker}", use_container_width=True):
                        st.session_state['trending_selected_ticker'] = ticker
                        st.session_state['auto_analyze'] = True
                        if 'stock_search' in st.session_state:
                            del st.session_state['stock_search']
                        st.rerun()
            else:
                st.info("📊 No trending stocks yet. Analyze some stocks to see popular choices!")
        else:
            st.caption("Trending data currently unavailable")
    except Exception as e:
        st.caption("⏳ Loading trending stocks...")

# Main content tabs
tab1, tab2 = st.tabs(["📊 Stock Analysis", "📚 Documentation"])

# Tab 1: Stock Analysis
with tab1:
    st.header(f"Analysis for {selected_ticker}" if selected_ticker else "Stock Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not selected_ticker:
            st.info("👈 Please search and select a stock from the sidebar to begin.")
        else:
            # Check for auto-analyze flag
            auto_analyze = st.session_state.get('auto_analyze', False)
            
            if st.button("🔍 Analyze Stock", type="primary", use_container_width=True) or auto_analyze:
                # Reset flag immediately
                if auto_analyze:
                    st.session_state['auto_analyze'] = False
                # Track steps and final data
                steps_list = []
                final_data = None
                
                try:
                    # Use st.status for progressive updates
                    with st.status(f"Analyzing {selected_ticker}...", expanded=True) as status:
                        # Stream from SSE endpoint
                        url = f"{API_URL}/stocks/{selected_ticker}/analysis-stream"
                        
                        with requests.get(url, stream=True, timeout=120) as response:
                            for line in response.iter_lines():
                                if line:
                                    decoded = line.decode('utf-8')
                                    
                                    # SSE format: "data: {json}"
                                    if decoded.startswith('data: '):
                                        try:
                                            event_data = json.loads(decoded[6:])
                                            event_type = event_data.get('type')
                                            
                                            if event_type == 'step':
                                                # Add step and show it
                                                step = event_data.get('step', {})
                                                steps_list.append(step)
                                                
                                                desc = step.get('description', 'Processing...')
                                                timestamp = step.get('timestamp', '')
                                                
                                                # Format timestamp
                                                time_str = ""
                                                duration_str = ""
                                                try:
                                                    dt = datetime.fromisoformat(timestamp)
                                                    time_str = dt.strftime("%H:%M:%S")
                                                    
                                                    # Calculate duration
                                                    if len(steps_list) > 1:
                                                        prev_step = steps_list[-2]
                                                        prev_ts = datetime.fromisoformat(prev_step.get('timestamp', ''))
                                                        duration = (dt - prev_ts).total_seconds()
                                                        duration_str = f" ({duration:.1f}s)"
                                                except:
                                                    pass
                                                
                                                st.write(f"✅ {desc} `{time_str}`{duration_str}")
                                            
                                            elif event_type == 'final':
                                                final_data = event_data.get('analysis', {})
                                            
                                            elif event_type == 'warning':
                                                msg = event_data.get('message', 'Warning')
                                                st.warning(f"⚠️ {msg}")
                                            
                                            elif event_type == 'error':
                                                msg = event_data.get('message', 'Error occurred')
                                                st.error(f"❌ {msg}")
                                                status.update(label=f"Analysis failed", state="error")
                                                break
                                                
                                        except json.JSONDecodeError as e:
                                            print(f"JSON decode error: {e}")
                                            continue
                        
                        # Update status
                        if final_data:
                            status.update(label=f"Analysis complete for {selected_ticker}", state="complete")
                        else:
                            status.update(label="Analysis failed - no data received", state="error")
                    
                    # Display results
                    if final_data:
                        st.markdown("### 🤖 AI Analysis")
                        
                        # Cache indicator
                        if final_data.get('cached'):
                            cache_time = final_data.get('cache_timestamp', '')
                            if cache_time:
                                try:
                                    dt = datetime.fromisoformat(cache_time)
                                    formatted_time = dt.strftime("%H:%M:%S")
                                    st.warning(f"⚡ Cached Result (from {formatted_time}) - New analysis available in < 1h")
                                except:
                                    st.warning("⚡ Cached Result")
                            else:
                                st.warning("⚡ Cached Result")
                        
                        st.markdown("---")
                        
                        # TOP SECTION: Metrics + Charts
                        col_left, col_right = st.columns([1, 2])
                        
                        with col_left:
                            st.subheader("📊 Key Metrics")
                            
                            # Price
                            current_price = final_data.get('current_price', 0)
                            currency = final_data.get('currency', 'INR')
                            st.metric("💰 Current Price", f"{currency} {current_price:,.2f}")
                            
                            # Sentiment
                            sentiment = final_data.get('sentiment', {})
                            classification = sentiment.get('classification', 'neutral')
                            confidence = sentiment.get('average_confidence', sentiment.get('confidence', 0.0))
                            
                            if classification.lower() == "insufficient data":
                                st.metric("📊 Sentiment", "NO DATA")
                                st.caption("Not enough news to analyze")
                            else:
                                if classification.lower() == "bullish":
                                    st.success(f"📈 Sentiment: **{classification.upper()}**")
                                elif classification.lower() == "bearish":
                                    st.error(f"📉 Sentiment: **{classification.upper()}**")
                                else:
                                    st.info(f"📊 Sentiment: **{classification.upper()}**")
                                
                                st.metric("🎯 Confidence Score", f"{confidence:.2%}")
                            
                            st.divider()
                            st.caption("**Day Range**")
                            day_low = final_data.get('day_low', 0)
                            day_high = final_data.get('day_high', 0)
                            st.write(f"{currency} {day_low:,.2f} - {currency} {day_high:,.2f}")
                        
                        with col_right:
                            st.subheader("📈 Price Charts")
                            
                            # Charts with tabs
                            multi_data = final_data.get('historical_data_multi', {})
                            
                            if multi_data:
                                tab1d, tab5d, tab1m, tab3m, tab1y = st.tabs([
                                    "📊 1 Day", "📊 5 Days", "📊 1 Month", "📊 3 Months", "📊 1 Year"
                                ])
                                
                                def create_candlestick_chart(period_data, title):
                                    if period_data and period_data.get('timestamps'):
                                        fig = make_subplots(
                                            rows=2, cols=1,
                                            row_heights=[0.7, 0.3],
                                            subplot_titles=(f'{title} - Price', 'Volume'),
                                            vertical_spacing=0.05,
                                            shared_xaxes=True
                                        )
                                        
                                        dates = [datetime.fromtimestamp(ts) for ts in period_data['timestamps']]
                                        fig.add_trace(
                                            go.Candlestick(
                                                x=dates,
                                                open=period_data['opens'],
                                                high=period_data['highs'],
                                                low=period_data['lows'],
                                                close=period_data['closes'],
                                                name='Price',
                                                increasing_line_color='#26a69a',
                                                decreasing_line_color='#ef5350'
                                            ),
                                            row=1, col=1
                                        )
                                        
                                        colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(period_data['closes'], period_data['opens'])]
                                        fig.add_trace(
                                            go.Bar(
                                                x=dates,
                                                y=period_data['volumes'],
                                                name='Volume',
                                                marker_color=colors,
                                                showlegend=False
                                            ),
                                            row=2, col=1
                                        )
                                        
                                        fig.update_layout(
                                            height=500,
                                            showlegend=False,
                                            xaxis_rangeslider_visible=False,
                                            hovermode='x unified',
                                            margin=dict(l=0, r=0, t=30, b=0)
                                        )
                                        
                                        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
                                        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
                                        
                                        return fig
                                    else:
                                        return None
                                
                                with tab1d:
                                    fig = create_candlestick_chart(multi_data.get('1d'), '1 Day')
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("📊 1-day data unavailable")
                                
                                with tab5d:
                                    fig = create_candlestick_chart(multi_data.get('5d'), '5 Days')
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("📊 5-day data unavailable")
                                
                                with tab1m:
                                    fig = create_candlestick_chart(multi_data.get('1mo'), '1 Month')
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("📊 1-month data unavailable")
                                
                                with tab3m:
                                    fig = create_candlestick_chart(multi_data.get('3mo'), '3 Months')
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("📊 3-month data unavailable")
                                
                                with tab1y:
                                    fig = create_candlestick_chart(multi_data.get('1y'), '1 Year')
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("📊 1-year data unavailable")
                            else:
                                st.warning("📊 Historical chart data unavailable")
                        
                        # Technical Indicators
                        st.markdown("---")
                        st.subheader("📊 Technical Indicators")
                        
                        tech_analysis = final_data.get('technical_analysis')
                        if tech_analysis and 'indicators' in tech_analysis:
                            indicators = tech_analysis['indicators']
                            
                            col_rsi, col_macd, col_bb = st.columns(3)
                            
                            with col_rsi:
                                if 'rsi' in indicators:
                                    rsi_data = indicators['rsi']
                                    rsi_val = rsi_data.get('value', 0)
                                    rsi_signal = rsi_data.get('signal', 'Unknown')
                                    
                                    st.metric("📈 RSI (14)", f"{rsi_val}", delta=rsi_signal)
                                    
                                    if rsi_val > 0:
                                        progress_color = "🔴" if rsi_val > 70 else "🟢" if rsi_val < 30 else "🟡"
                                        st.progress(min(rsi_val/100, 1.0))
                                        st.caption(f"{progress_color} {rsi_signal}")
                                else:
                                    st.info("RSI data unavailable")
                            
                            with col_macd:
                                if 'macd' in indicators:
                                    macd_data = indicators['macd']
                                    macd_val = macd_data.get('macd', 0)
                                    signal_val = macd_data.get('signal', 0)
                                    histogram = macd_data.get('histogram', 0)
                                    trend = macd_data.get('trend', 'Unknown')
                                    
                                    st.metric("📊 MACD", f"{macd_val:.2f}", delta=trend)
                                    st.caption(f"Signal: {signal_val:.2f}")
                                    st.caption(f"Histogram: {histogram:.2f}")
                                else:
                                    st.info("MACD data unavailable")
                            
                            with col_bb:
                                if 'bollinger_bands' in indicators:
                                    bb_data = indicators['bollinger_bands']
                                    upper = bb_data.get('upper', 0)
                                    middle = bb_data.get('middle', 0)
                                    lower = bb_data.get('lower', 0)
                                    position = bb_data.get('position', 'Unknown')
                                    
                                    st.metric("📉 Bollinger Bands", "")
                                    st.write(f"**Position:** {position}")
                                    st.caption(f"Upper: ₹{upper:,.2f}")
                                    st.caption(f"Middle: ₹{middle:,.2f}")
                                    st.caption(f"Lower: ₹{lower:,.2f}")
                                else:
                                    st.info("Bollinger Bands unavailable")
                        else:
                            st.info("⏳ Technical indicators are being calculated...")
                        
                        st.markdown("---")
                        
                        # AI Analysis Text
                        st.subheader("🤖 AI Analysis")
                        st.write(final_data['analysis'])

                        st.divider()

                        # Key Insights
                        st.subheader("📊 Recent Trends & Key Insights")
                        insights = final_data.get('key_insights', [])
                        if insights:
                            for insight in insights:
                                if "positive" in insight.lower() or "growth" in insight.lower() or "up" in insight.lower():
                                    st.success(f"📈 {insight}")
                                elif "risk" in insight.lower() or "concern" in insight.lower() or "down" in insight.lower():
                                    st.error(f"📉 {insight}")
                                else:
                                    st.info(f"ℹ️ {insight}")
                        else:
                            st.write("No specific trends identified.")

                        st.divider()

                        # Prediction
                        if final_data.get('prediction'):
                            st.subheader("🔮 Future Outlook & Prediction")
                            st.info(final_data.get('prediction'))
                            
                        # Risk Factors
                        st.subheader("⚠️ Risk Factors")
                        for risk in final_data.get('risk_factors', []):
                            st.write(f"- {risk}")
                        
                        # References
                        if 'references' in final_data and final_data['references']:
                            st.subheader(f"📚 References ({len(final_data['references'])})")
                            for idx, ref in enumerate(final_data['references'], 1):
                                source = ref.get('source', 'Unknown')
                                ticker_ref = ref.get('ticker', '')
                                url = ref.get('url', '#')
                                timestamp = ref.get('timestamp', '')
                                
                                if timestamp:
                                    try:
                                        from datetime import datetime
                                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        formatted_date = dt.strftime('%Y-%m-%d')
                                    except:
                                        formatted_date = timestamp[:10] if len(timestamp) >= 10 else timestamp
                                else:
                                    formatted_date = "Unknown date"
                                
                                if 'duckduckgo' in source.lower() or 'search' in source.lower():
                                    if url and url != '#':
                                        st.markdown(f"{idx}. 🔍 [{source}]({url}) - {formatted_date}")
                                    else:
                                        st.caption(f"{idx}. 🔍 {source} - {formatted_date}")
                                else:
                                    if url and url != '#':
                                        st.markdown(f"{idx}. [{source}]({url}) - {ticker_ref} ({formatted_date})")
                                    else:
                                        st.caption(f"{idx}. {source} - {ticker_ref} ({formatted_date})")
                        
                        st.success("✅ Analysis complete!")
                    else:
                        st.error("❌ No analysis data received. Please try again.")
                        
                except Exception as e:
                    st.error(f"Failed to get analysis: {e}")
    
    with col2:
        st.subheader("💡 Quick Info")
        st.info("""
        **How it works:**
        1. Search for a stock
        2. Scrapes latest news
        3. Uses AI to analyze
        4. Provides insights
        
        **Data Sources:**
        - DuckDuckGo Search
        - RSS Feeds
        - Financial APIs
        """)

# Tab 2: Documentation  
with tab2:
    st.header("📚 System Documentation")
    
    # Quick Navigation
    st.markdown("**Quick Links:** [Architecture](#architecture) | [Features](#features) | [APIs](#apis) | [Tech Stack](#tech-stack) | [Data Flow](#data-flow)")
    
    st.markdown("---")
    
    # ============================================================================
    # ARCHITECTURE
    # ============================================================================
    with st.expander("�️ System Architecture", expanded=True):
        st.markdown("""
        ### High-Level Architecture
        
        The system follows a **modern microservices architecture** with separation of concerns:
        
        ```
        ┌─────────────────┐
        │  Streamlit UI   │ ← User Interface (Python)
        └────────┬────────┘
                 │ HTTP/SSE
        ┌────────▼────────┐
        │   FastAPI       │ ← REST API + WebSocket
        │   Backend       │   (Python, Async)
        └────┬───┬───┬────┘
             │   │   │
        ┌────▼───▼───▼────────────────────┐
        │  Service Layer                   │
        │  • RAG (Analysis)                │
        │  • Stock API Service             │
        │  • Data Ingestion                │
        │  • Health Monitor                │
        └──┬────┬────┬────────────────┬───┘
           │    │    │                │
        ┌──▼──┐ │ ┌──▼────┐  ┌───────▼────┐
        │MySQL│ │ │ChromaDB│  │ External   │
        │  DB │ │ │Vector  │  │ APIs       │
        └─────┘ │ │   DB   │  │ • Stock    │
                │ └────────┘  │ • News     │
                │             │ • Search   │
        ┌───────▼──────┐      └────────────┘
        │ Azure OpenAI │
        │   GPT-4      │
        └──────────────┘
        ```
        
        **Components:**
        - **Frontend**: Streamlit (Real-time UI with SSE streaming)
        - **Backend**: FastAPI (Async REST API)
        - **Databases**: MySQL (metadata), ChromaDB (embeddings)
        - **AI**: Azure OpenAI GPT-4 (analysis), Sentence Transformers (embeddings)
        - **External APIs**: Stock APIs, News scrapers, Search engines
        """)
    
    # ============================================================================
    # FEATURES
    # ============================================================================
    with st.expander("✨ Key Features"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 📊 Stock Analysis
            - **Real-time Stock Data**: Live quotes from 4 APIs
            - **AI-Powered Insights**: GPT-4 analysis with RAG
            - **Multi-timeframe Charts**: 1D, 5D, 1M, 3M, 1Y candlesticks
            - **Technical Indicators**: RSI, MACD, Bollinger Bands
            - **Sentiment Analysis**: News sentiment classification
            - **Trending Stocks**: Popular stocks dashboard
            
            #### 🔍 Data Sources
            - **Stock APIs**: Finnhub, Alpha Vantage, Marketstack, Yahoo Finance
            - **News Scraping**: DuckDuckGo Search, RSS feeds
            - **Automatic Fallback**: Multi-API redundancy
            - **Smart Caching**: 1-hour analysis cache
            """)
        
        with col2:
            st.markdown("""
            #### 🏥 Health Monitoring
            - **Real-time Health Checks**: Every 5 minutes
            - **Uptime Tracking**: Per-source uptime %
            - **Latency Monitoring**: Response time tracking
            - **Database Status**: MySQL + ChromaDB health
            - **API Status**: Individual API health
            - **Error Tracking**: Recent failures with details
            
            #### 🚀 Performance
            - **Async Processing**: Non-blocking I/O
            - **SSE Streaming**: Real-time progress updates
            - **Vector Search**: Fast semantic similarity
            - **Query Expansion**: Smart search terms
            """)
    
    # ============================================================================
    # APIs
    # ============================================================================
    with st.expander("🔌 API Documentation"):
        st.markdown("""
        ### Backend REST API (FastAPI)
        
        **Base URL**: `http://localhost:8000`
        
        #### Stock Endpoints
        
        | Endpoint | Method | Description |
        |----------|--------|-------------|
        | `/stocks/search` | GET | Search stocks by name/symbol |
        | `/stocks/{ticker}/analysis` | GET | Get AI analysis (cached) |
        | `/stocks/{ticker}/analysis-stream` | GET | Stream analysis with SSE |
        | `/stocks/trending` | GET | Get trending stocks |
        
        **Example:**
        ```bash
        # Search for stocks
        curl "http://localhost:8000/stocks/search?q=Apple&country=United%20States"
        
        # Get analysis
        curl "http://localhost:8000/stocks/AAPL/analysis"
        
        # Stream analysis (Server-Sent Events)
        curl "http://localhost:8000/stocks/AAPL/analysis-stream"
        ```
        
        #### Health Endpoints
        
        | Endpoint | Method | Description |
        |----------|--------|-------------|
        | `/health` | GET | Backend & database status |
        | `/health/sources` | GET | All data source health |
        | `/health/summary` | GET | Category-level summary |
        | `/health/check-now` | POST | Trigger manual check |
        
        **Example:**
        ```bash
        # Get overall health
        curl "http://localhost:8000/health"
        
        # Get data source health
        curl "http://localhost:8000/health/sources"
        ```
        
        ### External APIs Used
        
        #### Stock Data APIs
        1. **Finnhub** - Real-time quotes, news (60 calls/min)
        2. **Alpha Vantage** - Global quotes (5 calls/min)
        3. **Marketstack** - EOD data (100 calls/month)
        4. **Yahoo Finance** - Free fallback (unlimited)
        
        #### News & Search
        1. **DuckDuckGo Search** - News aggregation
        2. **Google News RSS** - Stock news feeds
        3. **Moneycontrol RSS** - Indian market news
        4. **Economic Times RSS** - Business news
        
        #### AI Services
        1. **Azure OpenAI GPT-4** - Stock analysis
        2. **Sentence Transformers** - Text embeddings
        """)
    
    # ============================================================================
    # TECH STACK
    # ============================================================================
    with st.expander("�️ Technology Stack"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### Backend
            - **Framework**: FastAPI 0.104+
            - **Language**: Python 3.9+
            - **Async**: aiohttp, asyncio
            - **Web Server**: Uvicorn
            - **Validation**: Pydantic
            
            #### Databases
            - **SQL**: MySQL 8.0
            - **Vector DB**: ChromaDB
            - **Cache**: In-memory + file
            """)
        
        with col2:
            st.markdown("""
            #### Frontend
            - **Framework**: Streamlit
            - **Charts**: Plotly
            - **Components**: streamlit-searchbox
            
            #### AI/ML
            - **LLM**: Azure OpenAI GPT-4
            - **Embeddings**: all-MiniLM-L6-v2
            - **RAG**: ChromaDB + Langchain
            """)
        
        with col3:
            st.markdown("""
            #### DevOps
            - **Containerization**: Docker
            - **Orchestration**: Docker Compose
            - **Logging**: Loguru (JSON)
            - **Monitoring**: Custom health monitor
            
            #### Libraries
            - **Data**: Pandas, NumPy
            - **Web**: Requests, BeautifulSoup
            - **Search**: DuckDuckGo-search
            """)
    
    # ============================================================================
    # DATA FLOW
    # ============================================================================
    with st.expander("🔄 Data Flow & Processing"):
        st.markdown("""
        ### Stock Analysis Pipeline
        
        **Step 1: Stock Search**
        ```
        User Query → Alpha Vantage Search → Yahoo Finance → Web Search
                  ↓
        Return: Ticker, Name, Exchange
        ```
        
        **Step 2: Data Collection** (Async)
        ```
        Parallel Requests:
        ┌─ Stock APIs (Finnhub → Alpha Vantage → Marketstack → Yahoo)
        ├─ News Scraping (DuckDuckGo + RSS Feeds)
        └─ Historical Data (Finnhub → yfinance → Upstox)
        ```
        
        **Step 3: News Processing**
        ```
        Raw Articles → Extract Text → Generate Embeddings
                                    ↓
        Store in ChromaDB (Vector Database)
        ```
        
        **Step 4: AI Analysis (RAG)**
        ```
        Query: "Analysis for {ticker}"
           ↓
        1. Retrieve Relevant News (ChromaDB similarity search)
        2. Construct Prompt (stock data + news + technical indicators)
        3. GPT-4 Analysis (Azure OpenAI)
        4. Parse Response (analysis, insights, risks, prediction)
           ↓
        Cache Result (1 hour TTL)
        ```
        
        **Step 5: Streaming Response**
        ```
        SSE Stream:
        - step: "Fetching stock data..."
        - step: "Scraping news..."
        - step: "Analyzing with AI..."
        - final: {complete analysis}
        ```
        
        ### Health Monitoring Pipeline
        
        ```
        Background Task (Every 5 min):
           ↓
        For Each Data Source:
          ├─ Stock API → GET quote for test ticker
          ├─ RSS Feed → GET feed XML
          └─ Search → Query test term
           ↓
        Record:
          - Response time (ms)
          - Success/Failure
          - Error message
           ↓
        Calculate:
          - Uptime %
          - Avg response time
          - Current status (healthy/degraded/down)
        ```
        """)
    
    # ============================================================================
    # CONFIGURATION
    # ============================================================================
    with st.expander("⚙️ Configuration & Environment"):
        st.markdown("""
        ### Environment Variables
        
        Required variables in `.env` file:
        
        ```bash
        # Azure OpenAI (Required for AI analysis)
        AZURE_OPENAI_API_KEY=your_key_here
        AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
        AZURE_OPENAI_DEPLOYMENT=your_deployment_name
        AZURE_OPENAI_API_VERSION=2023-05-15
        
        # Stock APIs (At least one required)
        FINNHUB_API_KEY=your_finnhub_key
        ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
        MARKETSTACK_API_KEY=your_marketstack_key
        
        # Database (Required)
        MYSQL_ROOT_PASSWORD=root_password
        MYSQL_DATABASE=stockmarket_db
        MYSQL_USER=stockmarket_user
        MYSQL_PASSWORD=secure_password
        ```
        
        ### Data Source Configuration
        
        Edit `backend/config/sources.yaml` to:
        - Add/remove stock APIs
        - Configure RSS feeds
        - Adjust rate limits
        - Set timeouts
        
        ### Deployment
        
        **Development:**
        ```bash
        # Start all services
        docker-compose up -d
        
        # Run Streamlit
        streamlit run streamlit_app.py
        ```
        
        **Production:**
        - Use Docker Compose for orchestration
        - Set environment-specific `.env`
        - Configure reverse proxy (nginx)
        - Enable HTTPS
        - Set up monitoring/alerting
        """)
    
    # ============================================================================
    # TROUBLESHOOTING
    # ============================================================================
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        #### MySQL Disconnected
        **Symptoms**: "Database Status: Disconnected" in Health Monitor
        
        **Solutions**:
        1. Start MySQL container: `docker-compose up -d mysql`
        2. Check `.env` credentials match `docker-compose.yml`
        3. Verify port 3306 is not in use
        4. Check logs: `docker logs stockmarket_mysql`
        
        #### ChromaDB Disconnected
        **Symptoms**: "ChromaDB Status: Disconnected"
        
        **Solutions**:
        1. Restart backend: `docker-compose restart backend`
        2. Check ChromaDB directory permissions
        3. Clear ChromaDB cache: `rm -rf backend/chroma_db/`
        
        #### Stock APIs Down
        **Symptoms**: "Degraded" status in Health Monitor
        
        **Solutions**:
        1. Check API keys in `.env`
        2. Verify API rate limits not exceeded
        3. Check API service status (external)
        4. System will auto-fallback to other APIs
        
        #### Analysis Slow/Timeout
        **Symptoms**: Analysis takes >60s or times out
        
        **Solutions**:
        1. Check Azure OpenAI quota/limits
        2. Reduce news scraping depth
        3. Clear analysis cache
        4. Check network connectivity
        
        ### Logs Location
        
        - **Backend**: `docker logs stockmarket_backend`
        - **MySQL**: `docker logs stockmarket_mysql`
        - **Streamlit**: Terminal output
        - **Application**: `backend/logs/app.log`
        """)

