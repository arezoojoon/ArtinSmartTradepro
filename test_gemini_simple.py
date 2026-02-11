print("Starting script...")
import os
print("Importing dotenv...")
from dotenv import load_dotenv
print("Loading dotenv...")
load_dotenv(dotenv_path="backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {bool(api_key)}")

print("Importing google.generativeai...")
import google.generativeai as genai
print("Import complete.")

try:
    genai.configure(api_key=api_key)
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found model: {m.name}")
            break
    print("Gemini configured and listed successfully.")
except Exception as e:
    print(f"Configuration/Listing failed: {e}")
