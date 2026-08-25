import os
import asyncio
import random
import yaml
from pydub import AudioSegment
from engine.utils.logger import logger
from src.providers.tts.router import TTSRouter

class ScriptTooShortError(Exception):
    pass

class TTSEngine:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.audio_dir = os.path.join("output", "audio")
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        self.voices = [
            "en-US-ChristopherNeural",
            "en-US-GuyNeural",
            "en-US-EricNeural"
        ]
        self.tts_router = TTSRouter()

    async def generate_audio(self, script: str, timestamp: str):
        voice = random.choice(self.voices)
        logger.info(f"Generating TTS audio using voice: {voice}")
        
        audio_filename = f"{timestamp}.mp3"
        audio_path = os.path.join(self.audio_dir, audio_filename)
        
        # Configure edge-tts communicate
        rate = self.config['tts']['rate']
        pitch = self.config['tts']['pitch']
        volume = self.config['tts']['volume']
        
        await self.tts_router.synthesize(
            script, audio_path, voice=voice, rate=rate, pitch=pitch, volume=volume
        )
        
        processed_path = self._post_process_audio(audio_path)
        duration = self._get_duration(processed_path)
        
        return {
            "audio_path": processed_path,
            "duration_seconds": duration,
            "voice": voice
        }

    def _get_duration(self, path: str):
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0

    def _post_process_audio(self, path: str):
        audio = AudioSegment.from_file(path)
        duration = len(audio) / 1000.0
        
        logger.debug(f"Raw audio duration: {duration:.2f}s")
        
        if duration < 38.0:
            logger.warning(f"Audio too short ({duration:.2f}s), re-triggering generation.")
            raise ScriptTooShortError(f"Audio duration {duration:.2f}s is below minimum 38.0s")
        
        if duration > self.config['video']['duration_max']:
            logger.warning(f"Audio too long ({duration:.2f}s), trimming to 57s.")
            audio = audio[:57000]
            audio = audio.fade_out(300)
        
        # Normalize to -18 dBFS
        change_in_dbfs = -18.0 - audio.dBFS
        audio = audio.apply_gain(change_in_dbfs)
        
        # Save processed
        processed_filename = os.path.basename(path).replace(".mp3", "_processed.mp3")
        processed_path = os.path.join(self.audio_dir, processed_filename)
        audio.export(processed_path, format="mp3")
        
        # Clean up raw
        if os.path.exists(path):
            os.remove(path)
            
        return processed_path

if __name__ == "__main__":
    # Test block
    engine = TTSEngine()
    async def test():
        try:
            res = await engine.generate_audio("This is a test script for the viral content engine. It must be at least forty five seconds long to pass validation. Let's see if this works as expected.", "test_tts")
            print(res)
        except Exception as e:
            print(e)
    
    asyncio.run(test())
