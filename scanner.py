import argparse
import os
import sys
import subprocess
import time
import shutil
from PIL import ImageGrab
import pytesseract
import google.genai as genai
import ollama
import tkinter as tk
from tkinter import font as tkfont
from dotenv import load_dotenv

load_dotenv()

def show_fullscreen_alert(message):
    """Shows a high-impact full-screen alert that blocks input until dismissed."""
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg='#1a1a1a') # Modern dark background

    # Fonts
    title_font = tkfont.Font(family="Helvetica", size=56, weight="bold")
    msg_font = tkfont.Font(family="Helvetica", size=26)
    btn_font = tkfont.Font(family="Helvetica", size=20, weight="bold")
    
    # Center frame
    frame = tk.Frame(root, bg='#1a1a1a')
    frame.place(relx=0.5, rely=0.5, anchor='center')

    # Accent line
    tk.Frame(frame, height=4, width=400, bg='#ff4b2b').pack(pady=(0, 30))

    # Warning Header
    tk.Label(frame, text="STAY FOCUSED!", font=title_font, fg='#ff4b2b', bg='#1a1a1a').pack(pady=(0, 20))
    
    # AI Nudge Message
    tk.Label(frame, text=message, font=msg_font, fg='#e0e0e0', bg='#1a1a1a', 
             wraplength=900, justify="center").pack(pady=20)
    
    # Divider
    tk.Frame(frame, height=1, width=200, bg='#333333').pack(pady=30)

    # Dismiss behavior
    def dismiss():
        root.destroy()

    # Premium Button
    btn = tk.Button(frame, text="GOT IT, BACK TO WORK", command=dismiss, 
                    font=btn_font, bg='#ff4b2b', fg='white', 
                    padx=50, pady=20, borderwidth=0, 
                    cursor="hand2", activebackground='#ff6a4d', activeforeground='white')
    btn.pack(pady=20)

    # Keyboard shortcuts
    root.bind("<Escape>", lambda e: dismiss())
    root.bind("<Return>", lambda e: dismiss())

    root.mainloop()


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
        
        if sys.platform.startswith("win"):
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if not shutil.which("tesseract") and os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path

        text = pytesseract.image_to_string(image)
        if not text.strip():
            text = "[No readable text found on screen]"
        
        # 2. Ollama
        print("Starting Ollama service...")
        ollama_proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        
        # Checking model presence
        model_name = 'llama3.2:3b'
        model_present = False
        try:
            models_list = ollama.list()
            model_present = any(m.get('name', '').startswith(model_name) for m in models_list.get('models', []))
        except:
            pass

        if not model_present:
            print(f"Model {model_name} not found. Pulling...")
            subprocess.run(["ollama", "pull", model_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            model_present = True
        else:
            print(f"Model {model_name} is already present.")
        
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
        
        response = ollama.chat(model='llama3.2:3b', messages=[
            {'role': 'user', 'content': prompt},
        ])
        
        output = response['message']['content']
        
        print("Shutting down Ollama service...")
        ollama_proc.terminate()
        try:
            ollama_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_proc.kill()
            
        return output
    except Exception as e:
        if 'ollama_proc' in locals():
            ollama_proc.kill()
        return f"Error in offline analysis: {e}"

def analyze_online(image, goal):
    print("Running in ONLINE mode (Gemini)...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in .env"

    try:

        #OCR
        if sys.platform.startswith("win"):
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if not shutil.which("tesseract") and os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path

        text = pytesseract.image_to_string(image)
        #
        if not text.strip():
            text = "[No readable text found on screen]"
        
        client = genai.Client(api_key=api_key)
        
        for model in client.models.list():
            print(model.name)  # Lists like 'gemma-2-2b-it', 'gemini-2.5-flash'
        
        prompt = f"""
        The user's declared goal is: "{goal}".
        Look at this screenshot of their desktop.
        The text content visible on their screen is:
        ---
        {text[:1000]} 
        ---
        
        Are they working on it?
        If yes, just say "FOCUSED".
        If no, write a SHORT, QUIRKY, SARCASTIC nudge to get them back to work.
        """
        
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[prompt],
        )
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
             print(f"Distraction detected! Showing full screen alert.")
             show_fullscreen_alert(result)

if __name__ == "__main__":
    main()
