
def install_tool(name):
    print(f"\n[!] Attempting to install {name}...")
    
    if sys.platform == "win32":
        # Windows logic (winget)
        package_ids = {
            "Tesseract OCR": "UB_Software.TesseractOCR",
            "Ollama": "Ollama.Ollama"
        }
        pkg_id = package_ids.get(name)
        if not pkg_id: return False
        
        cmd = ["winget", "install", "--id", pkg_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"]
        print(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully installed {name}!")
            return True
        except Exception as e:
            print(f"Failed to install {name} via winget: {e}")
            return False

    elif sys.platform == "darwin":
        # macOS logic (homebrew)
        if not shutil.which("brew"):
            print("Error: Homebrew is not installed. Please install it first: https://brew.sh/")
            return False
        
        cmds = {
            "Tesseract OCR": ["brew", "install", "tesseract"],
            "Ollama": ["brew", "install", "--cask", "ollama"]
        }
        cmd = cmds.get(name)
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully installed {name}!")
            return True
        except Exception as e:
            print(f"Failed to install {name} via brew: {e}")
            return False

    elif sys.platform == "linux":
        # Linux logic with package manager detection
        try:
            if name == "Tesseract OCR":
                if shutil.which("apt-get"):
                    print("Detected Debian/Ubuntu (apt)")
                    subprocess.run(["sudo", "apt-get", "update"], check=True)
                    subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"], check=True)
                elif shutil.which("pacman"):
                    print("Detected Arch Linux (pacman)")
                    subprocess.run(["sudo", "pacman", "-Sy", "--noconfirm", "tesseract"], check=True)
                elif shutil.which("dnf"):
                    print("Detected Fedora/RHEL (dnf)")
                    subprocess.run(["sudo", "dnf", "install", "-y", "tesseract"], check=True)
                else:
                    print("Error: Could not determine package manager. Please install Tesseract manually.")
                    return False
            elif name == "Ollama":
                print("Running official Ollama installer: curl -fsSL https://ollama.com/install.sh | sh")
                subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
            
            print(f"Successfully installed {name}!")
            return True
        except Exception as e:
            print(f"Failed to install {name}: {e}")
            return False
            
    return False

def check_requirements():
    """Check if external tools are available and offer to install them based on OS."""
    tools = {
        "tesseract": "Tesseract OCR",
        "ollama": "Ollama"
    }
    
    for bin_name, formal_name in tools.items():
        if not shutil.which(bin_name):
            print(f"\n[!] {formal_name} not found in PATH.")
            choice = input(f"Would you like to try installing {formal_name} for {sys.platform}? (y/n): ").strip().lower()
            if choice == 'y':
                install_tool(formal_name)
        else:
            print(f"[✓] {formal_name} is available.")
