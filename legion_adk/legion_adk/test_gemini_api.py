# test_gemini_api.py
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gemini_api():
    """Test Gemini API with both old and new SDKs"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("❌ No GEMINI_API_KEY found in environment")
        return
    
    # Mask API key for display
    masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else "***"
    print(f"API Key (masked): {masked_key}")
    
    # Test 1: Try new Google Gen AI SDK
    print("\n=== Testing New Google Gen AI SDK ===")
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash-001',
            contents='Say "Hello from Gemini 2.0 Flash!" and nothing else.'
        )
        
        print("✅ New SDK Success!")
        print(f"Response: {response.text}")
        
    except ImportError:
        print("⚠️  New Google Gen AI SDK not installed")
        print("   Install with: pip install google-genai")
    except Exception as e:
        print(f"❌ New SDK failed: {e}")
    
    # Test 2: Try legacy google.generativeai SDK
    print("\n=== Testing Legacy Google Generative AI SDK ===")
    try:
        import google.generativeai as genai_legacy
        
        genai_legacy.configure(api_key=api_key)
        
        model = genai_legacy.GenerativeModel('gemini-2.0-flash-001')
        response = await model.generate_content_async('Say "Hello from Gemini 2.0 Flash via legacy SDK!" and nothing else.')
        
        print("✅ Legacy SDK Success!")
        print(f"Response: {response.text}")
        
    except ImportError:
        print("⚠️  Legacy Google Generative AI SDK not installed")
        print("   Install with: pip install google-generativeai")
    except Exception as e:
        print(f"❌ Legacy SDK failed: {e}")
    
    # Test 3: Direct curl test
    print("\n=== Testing Direct API Call ===")
    try:
        import aiohttp
        import json
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Say 'Hello from direct API call!' and nothing else."
                        }
                    ]
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text')
                    print("✅ Direct API Success!")
                    print(f"Response: {text}")
                else:
                    error_text = await response.text()
                    print(f"❌ Direct API failed with status {response.status}")
                    print(f"Error: {error_text}")
                    
    except ImportError:
        print("⚠️  aiohttp not installed for direct API test")
        print("   Install with: pip install aiohttp")
    except Exception as e:
        print(f"❌ Direct API failed: {e}")

    print("\n=== Summary ===")
    print("If any test succeeded, your API key is working!")
    print("If all tests failed, check:")
    print("1. API key is correct")
    print("2. API key has proper permissions")
    print("3. No rate limiting")
    print("4. Network connectivity")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())