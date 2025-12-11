"""
Data Source Health Monitor - Streamlit Page
Real-time monitoring dashboard for external data sources
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="System Health Monitor",
    page_icon="🏥",
    layout="wide"
)

# API Base URL
API_BASE_URL = "http://localhost:8000"


def get_status_color(status):
    """Get color for status"""
    colors = {
        "healthy": "#00C851",
        "degraded": "#ffbb33",
        "down": "#ff4444",
        "unknown": "#888888"
    }
    return colors.get(status.lower(), "#888888")


def get_status_emoji(status):
    """Get emoji for status"""
    emojis = {
        "healthy": "✅",
        "degraded": "⚠️",
        "down": "❌",
        "unknown": "❓"
    }
    return emojis.get(status.lower(), "❓")


def fetch_health_data():
    """Fetch health data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health/sources", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch health data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None


def fetch_summary():
    """Fetch health summary from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health/summary", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return None


def trigger_health_check():
    """Trigger manual health check"""
    try:
        response = requests.post(f"{API_BASE_URL}/health/check-now", timeout=30)
        if response.status_code == 200:
            st.success("✅ Health check triggered successfully!")
            return True
        else:
            st.error(f"Failed to trigger health check: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error triggering health check: {e}")
        return False


# Main App
st.title("🏥 Data Source Health Monitor")
st.markdown("Real-time monitoring of external data sources (APIs, search engines, RSS feeds)")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    if st.button("🏥 Run Health Check Now", use_container_width=True):
        with st.spinner("Running health check..."):
            if trigger_health_check():
                time.sleep(2)
                st.rerun()
    
    st.markdown("---")
    
    auto_refresh = st.checkbox("Auto-refresh every 30s", value=False)
    
    st.markdown("---")
    st.markdown("### 📊 About")
    st.info("""
    This dashboard monitors the health and uptime of:
    - **Stock APIs** (Finnhub, Alpha Vantage, Marketstack)
    - **Search Engines** (DuckDuckGo)
    - **RSS Feeds** (Moneycontrol, ET)
    
    Health checks run automatically every 5 minutes.
    """)

# Auto-refresh logic
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Fetch data
with st.spinner("Loading health data..."):
    health_data = fetch_health_data()
    summary = fetch_summary()
    
    # Also fetch backend health
    try:
        backend_health = requests.get(f"{API_BASE_URL}/health", timeout=5).json()
    except:
        backend_health = None

if not health_data or not summary:
    st.error("❌ Unable to load health data. Please ensure the backend is running.")
    st.stop()

# ============================================================================
# SECTION 1: BACKEND & DATABASES
# ============================================================================
st.markdown("## 🖥️ Backend & Databases")

col_backend, col_mysql, col_chroma = st.columns(3)

# Backend API Status
with col_backend:
    st.markdown("### 🌐 Backend API")
    if backend_health:
        status = backend_health.get('status', 'unknown')
        if status == "healthy":
            st.success("**Status:** ✅ Online")
        elif status == "degraded":
            st.warning("**Status:** ⚠️ Degraded")
        else:
            st.error("**Status:** ❌ Offline")
        
        st.info("""
        **Services:**
        - REST API
        - WebSocket
        - SSE Streaming
        """)
    else:
        st.error("**Status:** ❌ Offline")
        st.warning("Cannot connect to backend")

# MySQL Database
with col_mysql:
    st.markdown("### 🗄️ MySQL")
    if backend_health:
        databases = backend_health.get("databases", {})
        mysql_info = databases.get("mysql", {})
        mysql_connected = mysql_info.get("connected", False)
        
        if mysql_connected:
            st.success("**Status:** ✅ Connected")
            st.info("""
            **Stores:**
            - Stock metadata
            - User data
            - Cache
            """)
        else:
            st.error("**Status:** ❌ Disconnected")
            mysql_error = mysql_info.get("error")
            if mysql_error:
                with st.expander("Error Details"):
                    st.code(mysql_error[:100], language="text")
    else:
        st.warning("**Status:** ❓ Unknown")

# ChromaDB
with col_chroma:
    st.markdown("### 🧠 ChromaDB")
    if backend_health:
        chroma_info = databases.get("chromadb", {})
        chroma_connected = chroma_info.get("connected", False)
        doc_count = chroma_info.get("document_count", 0)
        
        if chroma_connected:
            st.success("**Status:** ✅ Connected")
            st.metric("Documents", f"{doc_count:,}")
            st.info("""
            **Stores:**
            - News embeddings
            - Historical data
            """)
        else:
            st.error("**Status:** ❌ Disconnected")
    else:
        st.warning("**Status:** ❓ Unknown")

st.markdown("---")

# ============================================================================
# SECTION 2: DATA SOURCES (APIs & Scraping/News)
# ============================================================================
st.markdown("## 📡 External Data Sources")

# Summary - Two Category Cards
st.markdown("## 📊 Overview")

# Get category stats
categories = summary.get('categories', {})
stock_apis_stats = categories.get('stock_apis', {})
scraping_news_stats = categories.get('scraping_news', {})

col_left, col_right = st.columns(2)

# Stock APIs Card
with col_left:
    st.markdown("### 📈 Stock APIs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stock_apis_stats.get('count', 0))
    with col2:
        st.metric("✅ Healthy", stock_apis_stats.get('healthy', 0))
    with col3:
        uptime = stock_apis_stats.get('uptime_percentage', 0)
        st.metric("Uptime", f"{uptime:.1f}%")
    
    # Response time
    avg_response = stock_apis_stats.get('avg_response_time_ms', 0)
    st.metric("Avg Response Time", f"{avg_response:.0f}ms")
    
    # Status badges
    if stock_apis_stats.get('down', 0) > 0:
        st.error(f"❌ {stock_apis_stats.get('down', 0)} Down")
    elif stock_apis_stats.get('degraded', 0) > 0:
        st.warning(f"⚠️ {stock_apis_stats.get('degraded', 0)} Degraded")
    else:
        st.success("✅ All Systems Operational")

# Scraping & News Card
with col_right:
    st.markdown("### 🔍 Scraping & News")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", scraping_news_stats.get('count', 0))
    with col2:
        st.metric("✅ Healthy", scraping_news_stats.get('healthy', 0))
    with col3:
        uptime = scraping_news_stats.get('uptime_percentage', 0)
        st.metric("Uptime", f"{uptime:.1f}%")
    
    # Response time
    avg_response = scraping_news_stats.get('avg_response_time_ms', 0)
    st.metric("Avg Response Time", f"{avg_response:.0f}ms")
    
    # Status badges
    if scraping_news_stats.get('down', 0) > 0:
        st.error(f"❌ {scraping_news_stats.get('down', 0)} Down")
    elif scraping_news_stats.get('degraded', 0) > 0:
        st.warning(f"⚠️ {scraping_news_stats.get('degraded', 0)} Degraded")
    else:
        st.success("✅ All Systems Operational")

st.markdown("---")

# Category Health Gauges
st.markdown("## 🎯 Health by Category")

col_gauge1, col_gauge2 = st.columns(2)

with col_gauge1:
    st.markdown("### 📈 Stock APIs Uptime")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stock_apis_stats.get('uptime_percentage', 0),
        title={'text': "Stock APIs Uptime %"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "royalblue"},
            'steps': [
                {'range': [0, 50], 'color': "#ff4444"},
                {'range': [50, 80], 'color': "#ffbb33"},
                {'range': [80, 100], 'color': "#00C851"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    fig.update_layout(height=250)
    st.plotly_chart(fig, use_container_width=True)

with col_gauge2:
    st.markdown("### 🔍 Scraping & News Uptime")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=scraping_news_stats.get('uptime_percentage', 0),
        title={'text': "Scraping & News Uptime %"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 50], 'color': "#ff4444"},
                {'range': [50, 80], 'color': "#ffbb33"},
                {'range': [80, 100], 'color': "#00C851"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    fig.update_layout(height=250)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Filter by category
st.markdown("## 🔍 Data Sources by Category")
category_filter = st.radio(
    "Filter by type:",
    ["All", "Stock APIs", "Search Engines", "RSS Feeds"],
    horizontal=True
)

# Filter data
if category_filter != "All":
    type_map = {
        "Stock APIs": "stock_api",
        "Search Engines": "search",
        "RSS Feeds": "rss"
    }
    filtered_data = [s for s in health_data if s['source_type'] == type_map[category_filter]]
else:
    filtered_data = health_data

# Detailed Source Cards
st.markdown("## 📋 Detailed Status")

for source in filtered_data:
    with st.expander(f"{get_status_emoji(source['current_status'])} {source['source_name']}", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**Status:** {get_status_emoji(source['current_status'])} {source['current_status'].upper()}")
            st.markdown(f"**Type:** {source['source_type']}")
        
        with col2:
            st.markdown(f"**Uptime:** {source['uptime_percentage']:.2f}%")
            st.markdown(f"**Avg Response:** {source['avg_response_time_ms']}ms")
        
        with col3:
            st.markdown(f"**Total Checks:** {source['total_checks']}")
            st.markdown(f"**✅ Success:** {source['successful_checks']}")
        
        with col4:
            st.markdown(f"**❌ Failures:** {source['failed_checks']}")
            last_check = source['last_check']
            if last_check != "Never":
                try:
                    dt = datetime.fromisoformat(last_check)
                    last_check_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    last_check_str = last_check
            else:
                last_check_str = "Never"
            st.markdown(f"**Last Check:** {last_check_str}")
        
        # Recent checks timeline
        if source['recent_checks']:
            st.markdown("### 📈 Recent Checks")
            recent_checks_data = []
            for check in source['recent_checks']:
                try:
                    dt = datetime.fromisoformat(check['timestamp'])
                    recent_checks_data.append({
                        'Time': dt.strftime("%H:%M:%S"),
                        'Status': check['status'],
                        'Response (ms)': check.get('response_time_ms', 'N/A'),
                        'Error': check.get('error_message', '')
                    })
                except:
                    pass
            
            if recent_checks_data:
                df = pd.DataFrame(recent_checks_data)
                
                # Color code status
                def highlight_status(row):
                    if row['Status'] == 'healthy':
                        return ['background-color: #d4edda'] * len(row)
                    elif row['Status'] == 'degraded':
                        return ['background-color: #fff3cd'] * len(row)
                    elif row['Status'] == 'down':
                        return ['background-color: #f8d7da'] * len(row)
                    else:
                        return [''] * len(row)
                
                st.dataframe(
                    df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Last error if any
        if source['last_error']:
            st.warning(f"**Last Error:** {source['last_error']}")

# Uptime Comparison Chart
st.markdown("## 📊 Uptime Comparison")
uptime_data = pd.DataFrame([
    {
        'Source': s['source_name'],
        'Uptime %': s['uptime_percentage'],
        'Type': s['source_type'],
        'Status': s['current_status']
    }
    for s in filtered_data
])

if not uptime_data.empty:
    fig = px.bar(
        uptime_data,
        x='Source',
        y='Uptime %',
        color='Status',
        color_discrete_map={
            'healthy': '#00C851',
            'degraded': '#ffbb33',
            'down': '#ff4444',
            'unknown': '#888888'
        },
        title="Uptime Percentage by Source"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Response Time Comparison
st.markdown("## ⚡ Response Time Comparison")
response_data = pd.DataFrame([
    {
        'Source': s['source_name'],
        'Avg Response (ms)': s['avg_response_time_ms'],
        'Type': s['source_type']
    }
    for s in filtered_data
    if s['avg_response_time_ms'] > 0
])

if not response_data.empty:
    fig = px.bar(
        response_data,
        x='Source',
        y='Avg Response (ms)',
        color='Type',
        title="Average Response Time by Source"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"Data refreshes automatically every 5 minutes. Last check: {summary.get('last_check', 'Unknown')}")
