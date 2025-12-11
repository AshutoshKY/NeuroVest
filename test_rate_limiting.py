#!/usr/bin/env python3
"""
Rate Limiting Verification Test
Tests that rate limits actually block requests after threshold
"""
import requests
import time

API_URL = "http://localhost:8000"

def test_rate_limiting():
    """Test that rate limiting blocks after 20 requests/minute"""
    print("=" * 70)
    print("RATE LIMITING TEST - Making 25 rapid requests")
    print("Expected: First 20 succeed, requests 21-25 get HTTP 429")
    print("=" * 70)
    
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    
    results = []
    
    # Make 25 rapid requests to /auth/me (which requires rate limiting)
    for i in range(1, 26):
        try:
            # Use a request that will fail auth but still hit rate limiter
            response = requests.get(
                f"{API_URL}/auth/login",
                timeout=5
            )
            
            if response.status_code == 405:  # Method Not Allowed (GET on POST endpoint)
                success_count += 1
                status = f"✅ Request {i}: Allowed (405)"
            elif response.status_code == 429:
                rate_limited_count += 1
                retry_after = response.headers.get('Retry-After', 'N/A')
                status = f"🚫 Request {i}: RATE LIMITED (429) - Retry-After: {retry_after}s"
            else:
                status = f"⚠️  Request {i}: Unexpected status {response.status_code}"
                
            results.append(status)
            print(status)
            
            # Small delay to ensure requests are counted
            time.sleep(0.05)
            
        except requests.exceptions.Timeout:
            error_count += 1
            status = f"❌ Request {i}: Timeout"
            results.append(status)
            print(status)
        except Exception as e:
            error_count += 1
            status = f"❌ Request {i}: Error - {e}"
            results.append(status)
            print(status)
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total requests sent: 25")
    print(f"Successful (allowed): {success_count}")
    print(f"Rate limited (429): {rate_limited_count}")
    print(f"Errors: {error_count}")
    print()
    
    if rate_limited_count >= 5:
        print("✅ PASS - Rate limiting is working!")
        print(f"   {rate_limited_count} requests were blocked after hitting the limit")
        return True
    else:
        print("❌ FAIL - Rate limiting not working properly")
        print(f"   Only {rate_limited_count} requests were blocked (expected 5+)")
        return False

if __name__ == "__main__":
    success = test_rate_limiting()
    exit(0 if success else 1)
