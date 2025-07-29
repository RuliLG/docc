#!/usr/bin/env python3
import asyncio
import httpx

async def test_api():
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("Testing API endpoints...")
        
        # Test health check
        print("\n1. Health check:")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test voices endpoint
        print("\n2. Get voices:")
        try:
            response = await client.get(f"{base_url}/voices")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test cache stats
        print("\n3. Cache stats:")
        try:
            response = await client.get(f"{base_url}/cache/stats")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test TTS generation (will likely fail without API keys)
        print("\n4. Generate TTS (may fail without API keys):")
        try:
            response = await client.post(
                f"{base_url}/generate-audio",
                json={"text": "Hello, this is a test.", "voice": None}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())