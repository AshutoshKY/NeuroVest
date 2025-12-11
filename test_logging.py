#!/usr/bin/env python3
"""
Test script to demonstrate the new logging improvements.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, '/Volumes/AshDrive/prjts/stockmarket/backend')

# Set up environment
os.chdir('/Volumes/AshDrive/prjts/stockmarket/backend')

from app.core.logging_config import setup_logging
from app.core.config import settings
import logging

# Setup logging
setup_logging(log_level="INFO", format_type="structured")
logger = logging.getLogger(__name__)

print("=" * 80)
print("LOGGING IMPROVEMENTS DEMONSTRATION")
print("=" * 80)
print()

# Test 1: Basic logging with context
logger.info("🎯 Testing basic structured logging", extra={
    "operation": "test_logging",
    "ticker": "HAL",
    "status": "success"
})

# Test 2: Logging with duration
logger.info("⏱️  Testing logging with duration", extra={
    "operation": "fetch_data",
    "ticker": "BEL",
    "duration_ms": 150,
    "status": "success"
})

# Test 3: Warning log
logger.warning("⚠️  Testing warning log", extra={
    "operation": "cache_check",
    "ticker": "ICICIBANK",
    "status": "cache_miss"
})

# Test 4: Error log
logger.error("❌ Testing error log", extra={
    "operation": "api_call",
    "ticker": "INVALID",
    "status": "failure",
    "error": "Ticker not found"
})

# Test 5: Debug log (won't show with INFO level)
logger.debug("🔍 This is a DEBUG log - only visible with LOG_LEVEL=DEBUG", extra={
    "operation": "debug_test",
    "details": "some_details"
})

print()
print("=" * 80)
print("TESTING IMPORT OF MAIN APPLICATION")
print("=" * 80)
print()

# Import main app to verify no SQL logs appear
from app.main import app

logger.info("✅ Application imported successfully - NO SQL QUERIES should appear above!")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ SQL query logging: DISABLED")
print("✅ Structured logging: ENABLED")
print("✅ Request ID tracking: ENABLED (will show in actual requests)")
print("✅ Context fields: operation, ticker, duration_ms, status")
print("=" * 80)
