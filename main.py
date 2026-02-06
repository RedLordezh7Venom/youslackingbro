import time
import subprocess
import sys
from install_scripts import check_requirements

def main():
    print("--- Focus Assist Nudge ---")
    check_requirements()
    
    # 1. Get User Input
    goal = input("What is your focus goal right now? > ").strip()
    if not goal:
        print("You must have a goal!")
        return

    mode = input("Choose mode (online/offline) [default: offline] > ").strip().lower()
    if mode not in ["online", "offline"]:
        mode = "offline"
    
    print(f"\nOkay! I'll check on you every 5 minutes.")
    print(f"Goal: {goal}")
    print(f"Mode: {mode}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            print("zzzz... (waiting 5 mins)")
            time.sleep(5) 
            
            print("Waking up! Scanning screen...")
            # Run the scanner in a separate process
            subprocess.run([sys.executable, "scanner.py", "--goal", goal, "--mode", mode])
            
    except KeyboardInterrupt:
        print("\nStopping Focus Assist. Good luck!")

if __name__ == "__main__":
    main()
