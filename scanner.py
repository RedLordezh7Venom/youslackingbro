import argparse
import os
import sys
from PIL import ImageGrab
import pytesseract
import google.generativeai as genai
import ollama
from win11toast import toast
from dotenv import load_dotenv

load_dotenv()

def capture_screen():
    try:
        # Capture the entire screen
        screenshot = ImageGrab.grab()
        return screenshot
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None

def analyze_offline(image, goal):
    print("Running in OFFLINE mode (Ollama + Tesseract)...")
    try:
        # 1. OCR
        text = pytesseract.image_to_string(image)
        if not text.strip():
            text = "[No readable text found on screen]"
        
        # 2. Ollama
        prompt = f"""
        You are a focus assistant. The user's goal is: "{goal}".
        Here is the text content visible on their screen:
        
        ---
        {text[:2000]} 
        ---
        
        (Text truncated to 2000 chars for speed)
        
        Is the user working on their goal? 
        If YES, reply with "FOCUSED".
        If NO, reply with a SHORT, QUIRKY, SARCASTIC nudge to get them back to work.
        """
        
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': prompt},
        ])
        
        return response['message']['content']
    except Exception as e:
        return f"Error in offline analysis: {e}"

def analyze_online(image, goal):
    print("Running in ONLINE mode (Gemini)...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in .env"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        The user's declared goal is: "{goal}".
        Look at this screenshot of their desktop.
        Are they working on it?
        If yes, just say "FOCUSED".
        If no, write a SHORT, QUIRKY, SARCASTIC nudge to get them back to work.
        """
        
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error in online analysis: {e}"

def main():
    parser = argparse.ArgumentParser(description="Focus Assist Scanner")
    parser.add_argument("--goal", required=True, help="User's current focus goal")
    parser.add_argument("--mode", choices=["online", "offline"], default="offline", help="Analysis mode")
    
    args = parser.parse_args()
    
    print(f"Scanning... Goal: {args.goal}, Mode: {args.mode}")
    
    image = capture_screen()
    if not image:
        return

    if args.mode == "online":
        result = analyze_online(image, args.goal)
    else:
        result = analyze_offline(image, args.goal)

    print(f"Result: {result}")

    if "FOCUSED" not in result.upper():
        
        # User is distracted! Nudge them.
        # Clean up the response if it contains "FOCUSED" but not as the only thing, 
        # but usually if it's not focused it's a nudge. 
        # API might return "NO, they are..." so we should check for explicit positive affirmation.
        # But my prompt said "If yes, reply with FOCUSED". 
        # So any response NOT containing FOCUSED is likely a nudge.
        # To be safe, let's treat "FOCUSED" as the safe word.
        
        # Determine if we should toast
        if "FOCUSED" in result and len(result) < 20:
             # Likely just "FOCUSED" or "FOCUSED."
             pass
        else:
             # It's a nudge
             toast("Focus Nudge 🔔", result, duration="long")

if __name__ == "__main__":
    main()
