# Viral Content Engine 🎥

A production-grade, fully automated short-form video content engine in Python. Generates, composes, and publishes viral Reddit Mystery/Story narration videos over Minecraft parkour or Subway Surfers gameplay.

## 🚀 Pipeline Flow
**Script (Ollama)** → **TTS Voice (edge-tts)** → **Subtitles (Whisper)** → **Composition (FFmpeg)** → **Publishing (YouTube/IG/Email)**

## 🛠️ System Requirements
- **Python 3.10+**
- **FFmpeg**: Must be in system PATH.
- **Ollama**: Install from [ollama.com](https://ollama.com) and pull `llama3.2`.

## 📦 Setup Instructions
1. **Initialize Project**:
   ```bash
   python setup.py
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Fill in `.env` with your API keys and email credentials.
   - Add your YouTube `client_secret.json` to `config/credentials/`.
4. **Prepare Assets**:
   - Add Minecraft/Subway Surfers `.mp4` clips to `assets/backgrounds/`.
   - Add lofi/ambient `.mp3` tracks to `assets/music/`.

## 🎮 Usage
- **Test Generation**: `python main.py --test` (Generates video without uploading)
- **Run Once**: `python main.py --run-now` (Generates and publishes)
- **Start Scheduler**: `python main.py --schedule` (Runs every 4 hours forever)
- **Setup Check**: `python main.py --setup`

## 📁 Project Structure
- `src/`: Core logic (scripting, TTS, vision, uploader).
- `assets/`: Backgrounds, music, and fonts.
- `output/`: Generated scripts, audio, subtitles, and final videos.
- `config/`: Configuration YAML and credentials.

## ⚖️ Quality Standards
- Unique scripts every run (hash-checked hooks).
- Word-level synced captions with yellow highlighting.
- High-fidelity FFmpeg render (CRF 18).
- Error resilience with detailed logging.

## 📝 License
MIT License. Free to use and modify.
