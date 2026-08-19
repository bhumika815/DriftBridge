"""Test Gemini API key"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {api_key[:20]}...")
print(f"Key length: {len(api_key)}")

try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Translate 'Hello' to Hindi. Only provide the translation."
            }]
        }]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    if "candidates" in data:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        print("\n✅ API Key Working!")
        print(f"Translation test: {text}")
    else:
        print(f"\n❌ Unexpected response: {data}")
    
except Exception as e:
    print(f"\n❌ API Key Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response: {e.response.text}")

