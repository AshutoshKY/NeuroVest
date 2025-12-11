#!/usr/bin/env python3
"""
WebSocket client test script for real-time stock analysis.
"""
import asyncio
import websockets
import json


async def test_websocket_analysis():
    """Test WebSocket analysis endpoint."""
    uri = "ws://localhost:8000/ws/stocks/TCS/analysis"
    
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Receive welcome message
            welcome = await websocket.recv()
            print(f"📥 Welcome: {welcome}")
            
            # Send analyze command
            print("\n📤 Sending analyze request...")
            await websocket.send(json.dumps({"action": "analyze"}))
            
            # Receive progressive updates
            print("\n📊 Receiving updates:\n")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "progress":
                        progress = data.get("progress", 0)
                        step_msg = data.get("message", "")
                        print(f"  [{progress}%] {step_msg}")
                    
                    elif msg_type == "status":
                        print(f"  ℹ️  {data.get('message', '')}")
                    
                    elif msg_type == "complete":
                        print("\n✅ Analysis complete!")
                        analysis_data = data.get("data", {})
                        sentiment = analysis_data.get("sentiment", {})
                        print(f"   Sentiment: {sentiment.get('classification', 'N/A')}")
                        print(f"   Score: {sentiment.get('score', 'N/A')}")
                        break
                    
                    elif msg_type == "error":
                        print(f"\n❌ Error: {data.get('message', '')}")
                        break
                
                except asyncio.TimeoutError:
                    print("\n⏰ Timeout waiting for response")
                    break
            
            print("\n✅ Test complete!")
    
    except Exception as e:
        print(f"\n❌ Connection error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Analysis Test")
    print("=" * 60)
    asyncio.run(test_websocket_analysis())
