import argparse
import os
import sys
import subprocess
import time
import shutil
import io
import base64
from PIL import ImageGrab
from groq import Groq
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
    print("Running in OFFLINE mode (Ollama Vision)...")
    try:
        # Convert PIL image to bytes for Ollama
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        # 2. Ollama
        print("Starting Ollama service...")
        ollama_proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        
        model_name = 'qwen3-vl:2b'  # Lightweight vision model (~829MB)
        print(f"Ensuring model {model_name} is present...")
        subprocess.run(["ollama", "pull", model_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        prompt = f"""
        USER GOAL: "{goal}"
        
        Look at this screenshot. 
        DETERMINE: Is the user actually working on the specific goal?
        
        RULES:
        1. If they are working on the goal, reply with ONLY the word "FOCUSED".
        2. If NOT related, roast them with a biting, clever, and sarcastic nudge (max 20 words).
        3. TONE: Be condescending and witty. 
        4. NEVER explain your reasoning. NEVER say the word "DISTRACTION".
        """
        
        response = ollama.chat(model=model_name, messages=[
            {
                'role': 'user', 
                'content': prompt,
                'images': [img_bytes]
            },
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
    print("Running in ONLINE mode (Groq Vision)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not found in .env"

    try:
        # 1. Convert PIL image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        client = Groq(api_key=api_key)
        
        prompt = f"""
        You are a WITTY, HARSH, and HIGHLY SARCASTIC Productivity Coach. 
        Your job is to roast the user for being distracted.
        
        USER GOAL: "{goal}"
        
        Look at this screenshot of the user's desktop.
        DETERMINE: Is the user actually working on the specific goal?
        
        STRICT RULES:
        1. Identify the application or website in the foreground.
        2. If the PRIMARY content is related to the goal, reply with ONLY the word "FOCUSED".
        3. Ignore background windows or taskbars.
        4. If the MAIN activity is clearly NOT related, roast them with a biting, clever, and sarcastic nudge (max 20 words).
        5. TONE: Be sharp and condescending.
        6. NEVER provide extra commentary. NEVER say the word "DISTRACTION".
        7. If it is a NUDGE, DO NOT use the word FOCUS or FOCUSED.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        return chat_completion.choices[0].message.content
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
