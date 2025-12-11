#!/usr/bin/env python3
"""Test script to fetch stock data for watchlist"""
import requests
import json

# Test stocks
stocks = ["TCS.NS", "HAL.NS", "RELIANCE.NS"]

# Headers required by backend
headers = {
    "X-Device-Token": "test-device-123",
    "X-Session-ID": "test-session-456",
    "Content-Type": "application/json"
}

print("=" * 80)
print("TESTING STOCK API FOR WATCHLIST")
print("=" * 80)
print()

for stock in stocks:
    print(f"\n{'='*80}")
    print(f"STOCK: {stock}")
    print(f"{'='*80}\n")
    
    # Try stock info endpoint
    try:
        response = requests.get(
            f"http://localhost:8000/stocks/info/{stock}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print("\n" + "-"*80 + "\n")

print("\nTest complete!")
