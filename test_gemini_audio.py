import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# Load env
load_dotenv(dotenv_path="backend/.env")

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

def test_gemini_audio(file_path):
    print(f"Testing Gemini Audio with file: {file_path}")
    
    # 1. Upload File
    print("Uploading file...")
    start_time = time.time()
    try:
        audio_file = genai.upload_file(path=file_path)
        print(f"File uploaded: {audio_file.name}")
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    # 2. Generate Content
    print("Sending to Gemini 2.0 Flash...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = """
    Listen to this sales call audio.
    Return a JSON object with the following fields:
    {
        "transcript": "Full text transcript",
        "sentiment": "POSITIVE, NEUTRAL, or NEGATIVE",
        "intent": "Identify the primary intent (e.g. Purchase, Inquiry, Complaint)",
        "action_items": ["List of specific action items"],
        "confidence": 0.0 to 1.0 confidence score
    }
    """
    
    try:
        response = model.generate_content([prompt, audio_file])
        end_time = time.time()
        
        print("\n--- GEMINI RESPONSE ---")
        print(response.text)
        print("-----------------------")
        print(f"Latency: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    file_path = "test_sales_call.wav"
    if os.path.exists(file_path):
        test_gemini_audio(file_path)
    else:
        print(f"Error: {file_path} not found.")
