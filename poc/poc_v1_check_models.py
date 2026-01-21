
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 현재 폴더는 'poc'이므로 backend의 .env를 로드
load_dotenv("../backend/.env")

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
print(f"API Key Loaded: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    try:
        print("Listing models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No API Key found.")
