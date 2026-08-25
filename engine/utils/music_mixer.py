import os
import random
import subprocess
from engine.utils.logger import logger

class MusicMixer:
    def __init__(self, music_dir: str = "assets/music"):
        self.music_dir = music_dir
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)

    def mix_audio(self, tts_audio_path: str, duration: float, timestamp: str, volume_percent: int = 12):
        """Picks random music, loops it to match duration, and mixes with TTS."""
        music_files = [f for f in os.listdir(self.music_dir) if f.endswith(".mp3")]
        
        output_filename = f"temp_mixed_audio_{timestamp}.mp3"
        output_path = os.path.join("output", "audio", output_filename)

        vol_decimal = volume_percent / 100.0
        
        if not music_files:
            logger.warning("No background music found. Using TTS only.")
            # Just copy/link TTS to temp_mixed for consistency if no music
            cmd = ["ffmpeg", "-y", "-i", tts_audio_path, "-acodec", "libmp3lame", output_path]
        else:
            music_file = random.choice(music_files)
            music_path = os.path.join(self.music_dir, music_file)
            logger.info(f"Mixing music: {music_file} at {volume_percent}% vol")
            
            # amix filter: [0:a] is TTS, [1:a] is Music
            # [1:a]volume=0.12,aloop=loop=-1:size=2e+09[music];[0:a]volume=1.0[speech];[speech][music]amix=inputs=2:duration=first[aout]
            # Use -t to ensure output duration matches TTS
            cmd = [
                "ffmpeg", "-y",
                "-i", tts_audio_path,
                "-stream_loop", "-1", "-i", music_path,
                "-filter_complex", f"[0:a]volume=1.0[speech];[1:a]volume={vol_decimal}[music];[speech][music]amix=inputs=2:duration=first[aout]",
                "-map", "[aout]",
                "-t", str(duration),
                output_path
            ]
            
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
