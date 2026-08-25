import os
import subprocess
import sys
import requests
import shutil

def run_setup():
    print("=== Viral Content Engine Setup ===")
    
    # 1. Create directories
    dirs = [
        "config/credentials", "assets/backgrounds", "assets/music", "assets/fonts",
        "output/scripts", "output/audio", "output/subtitles", "output/thumbnails",
        "output/videos", "output/published", "output/logs", "output/pending_emails"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Directory ensured: {d}")

    # 2. Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("FFmpeg is installed and in PATH.")
    except:
        print("ERROR: FFmpeg not found! Please install FFmpeg and add it to your PATH.")
        print("Windows: winget install ffmpeg")
        print("Mac: brew install ffmpeg")

    # 3. Check Ollama
    try:
        resp = requests.get("http://localhost:11434/api/tags")
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            if "llama3.2:latest" in models or "llama3.2" in models:
                print("Ollama is running and llama3.2 is available.")
            else:
                print("WARNING: llama3.2 model not found in Ollama.")
                print("Action: run 'ollama pull llama3.2'")
    except:
        print("WARNING: Ollama is not running on localhost:11434.")

    # 4. Download Montserrat font
    font_path = "assets/fonts/Montserrat-Bold.ttf"
    if not os.path.exists(font_path):
        print("Downloading Montserrat-Bold.ttf...")
        font_url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
        try:
            r = requests.get(font_url)
            with open(font_path, "wb") as f:
                f.write(r.content)
            print("Font downloaded.")
        except Exception as e:
            print(f"Failed to download font: {e}")

    # 5. Create .env template
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# YouTube\nYOUTUBE_CLIENT_ID=\nYOUTUBE_CLIENT_SECRET=\n\n")
            f.write("# Instagram Graph API\nIG_USER_ID=\nIG_ACCESS_TOKEN=\n\n")
            f.write("# Email (for Snapchat delivery)\nEMAIL_ADDRESS=\nEMAIL_APP_PASSWORD=\nSNAPCHAT_EMAIL=\n")
        print(".env template created. Please fill in your keys.")

    print("\nSetup validation complete.")
    print("Next steps:")
    print("1. Add background videos (.mp4) to assets/backgrounds/")
    print("2. Add lofi music (.mp3) to assets/music/")
    print("3. Fill in .env with your API keys/email credentials")
    print("4. Add your YouTube client_secret.json to config/credentials/")
    print("5. Run: python main.py --test")

if __name__ == "__main__":
    run_setup()
