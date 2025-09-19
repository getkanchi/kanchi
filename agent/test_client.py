#!/usr/bin/env python3
"""
Simple WebSocket client for testing the Celery event monitor
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_client():
    uri = "ws://localhost:8765"
    
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        print("Connected! Listening for events...")
        print("-" * 50)
        
        # Send initial ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Listen for events
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Handle different message types
                if data.get('type') == 'connection':
                    print(f"[CONNECTION] {data.get('message')}")
                elif data.get('type') == 'pong':
                    print(f"[PONG] Server responded at {data.get('timestamp')}")
                elif 'task_id' in data:
                    # This is a task event
                    event_type = data.get('event_type', 'unknown')
                    task_name = data.get('task_name', 'unknown')
                    task_id = data.get('task_id', '')
                    
                    if event_type == 'task-succeeded':
                        runtime = data.get('runtime', 0)
                        print(f"✅ [{event_type}] {task_name}[{task_id[:8]}...] completed in {runtime:.2f}s")
                        if data.get('result'):
                            print(f"   Result: {data['result'][:100]}...")
                    elif event_type == 'task-failed':
                        print(f"❌ [{event_type}] {task_name}[{task_id[:8]}...] FAILED")
                        if data.get('exception'):
                            print(f"   Exception: {data['exception']}")
                    elif event_type == 'task-started':
                        print(f"🚀 [{event_type}] {task_name}[{task_id[:8]}...] started")
                    elif event_type == 'task-retried':
                        retries = data.get('retries', 0)
                        print(f"🔄 [{event_type}] {task_name}[{task_id[:8]}...] retry #{retries}")
                    else:
                        print(f"📦 [{event_type}] {task_name}[{task_id[:8]}...]")
                    
                    # Show additional details for verbose output
                    if event_type in ['task-failed', 'task-succeeded']:
                        print(f"   Args: {data.get('args', '()')}")
                        print(f"   Kwargs: {data.get('kwargs', '{}')}")
                        print(f"   Routing: {data.get('routing_key', 'default')}")
                else:
                    print(f"[MESSAGE] {json.dumps(data, indent=2)}")
                
                print("-" * 50)
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] Invalid JSON: {e}")
                print(f"[RAW] {message}")
            except Exception as e:
                print(f"[ERROR] {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_client())
    except KeyboardInterrupt:
        print("\nClient disconnected")
    except Exception as e:
        print(f"Error: {e}")