import os
import sys
import shutil
import logging
import time
import subprocess
from PIL import ImageGrab
import pytesseract
import ollama

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OfflineTest")

def run_test():
    goal = "ds algorithms study"
    logger.debug(f"Starting offline test. Goal: {goal}")

    if sys.platform.startswith("win"):
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if not shutil.which("tesseract") and os.path.exists(default_path):
            logger.debug(f"Tesseract not in PATH, but found at {default_path}. Setting it manually.")
            pytesseract.pytesseract.tesseract_cmd = default_path

    try:
        logger.debug("Attempting to capture screen...")
        screenshot = ImageGrab.grab()
        logger.debug(f"Screen captured: {screenshot.size} {screenshot.mode}")
    except Exception as e:
        logger.error(f"Screen capture failed: {e}")
        return

    try:
        logger.debug("Starting OCR with Tesseract...")
        text = pytesseract.image_to_string(screenshot)
        clean_text = text.strip()
        logger.debug(f"OCR complete. Characters found: {len(clean_text)}")
        if not clean_text:
            logger.warning("No text detected on screen.")
            clean_text = "[No readable text found on screen]"
        else:
            logger.debug(f"Snippet of OCR: {clean_text[:100]}...")
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return

    try:
        logger.debug("Starting Ollama service (ollama serve)...")
        # Start Ollama server in background
        ollama_proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.debug("Waiting 5 seconds for Ollama to initialize...")
        time.sleep(5)

        logger.debug("Prompting Ollama (llama3.2)...")
        prompt = f"""
        User's goal: "{goal}"
        Visible screen text: "{clean_text[:1500]}"
        Is the user focused? If so say "FOCUSED", else give a sarcastic nudge.
        """
        
        response = ollama.chat(model='llama3.2:3b', messages=[
            {'role': 'user', 'content': prompt},
        ])
        
        result = response['message']['content']
        logger.info(f"Ollama Response: {result}")

        # Kill the service
        logger.debug("Shutting down Ollama service...")
        ollama_proc.terminate()
        ollama_proc.wait(timeout=5)
    except Exception as e:
        logger.error(f"Ollama task failed: {e}")
        if 'ollama_proc' in locals():
            ollama_proc.kill()

if __name__ == "__main__":
    run_test()
