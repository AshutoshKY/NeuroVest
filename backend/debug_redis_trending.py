import redis
import time
from datetime import datetime

def inspect_trending():
    try:
        # Try localhost first
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis at localhost:6379")
    except Exception as e:
        print(f"❌ Could not connect to localhost: {e}")
        return

    current_time = time.time()
    
    # 1. Inspect New Sliding Window Key
    print("\n--- 🆕 KEY: trending:window (New Sliding Window) ---")
    if not r.exists("trending:window"):
        print("Key 'trending:window' does NOT exist.")
    else:
        # Get all events
        events = r.zrange("trending:window", 0, -1, withscores=True)
        if not events:
            print("Key exists but is empty.")
        else:
            print(f"Found {len(events)} events.")
            print(f"{'TICKER':<10} | {'TIMESTAMP':<20} | {'AGE (min)':<10} | {'EXPIRES IN (min)':<15}")
            print("-" * 65)
            
            for member, score in events:
                # member is "TICKER:TIMESTAMP"
                if ":" in member:
                    ticker = member.split(":")[0]
                else:
                    ticker = member
                
                age_seconds = current_time - score
                age_minutes = age_seconds / 60
                expires_in_minutes = (3600 - age_seconds) / 60
                
                status = "✅ ACTIVE" if age_seconds < 3600 else "❌ EXPIRED (Will be removed on next read)"
                
                print(f"{ticker:<10} | {score:<20} | {age_minutes:<10.2f} | {expires_in_minutes:<15.2f} -> {status}")

    # 2. Inspect Old Legacy Key
    print("\n--- 👴 KEY: trending:stocks (Old Legacy Counter) ---")
    if not r.exists("trending:stocks"):
        print("Key 'trending:stocks' does NOT exist.")
    else:
        items = r.zrange("trending:stocks", 0, -1, withscores=True)
        print(f"Found {len(items)} items (These are independent counters, no expiry time).")
        for member, score in items:
            print(f"{member}: {score}")

if __name__ == "__main__":
    inspect_trending()
