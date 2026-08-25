import os
import random
import subprocess
import json
from engine.utils.logger import logger

class BackgroundManager:
    def __init__(self, backgrounds_dir: str = "assets/backgrounds"):
        self.backgrounds_dir = backgrounds_dir
        if not os.path.exists(self.backgrounds_dir):
            os.makedirs(self.backgrounds_dir)

    def select_and_trim(self, duration: float, timestamp: str):
        """Randomly selects a background video, picks a random start, and trims it."""
        files = [f for f in os.listdir(self.backgrounds_dir) if f.endswith(".mp4")]
        if not files:
            logger.warning("No background videos found in assets/backgrounds/")
            # Fallback for testing: if no video, we'll let it fail or provide a dummy color black
            raise FileNotFoundError("No background videos found. Please add .mp4 files to assets/backgrounds/")
            
        bg_video = random.choice(files)
        bg_path = os.path.join(self.backgrounds_dir, bg_video)
        
        # Get video duration using ffprobe
        logger.debug(f"Selected background: {bg_video}")
        video_len = self._get_video_duration(bg_path)
        
        # Random start point: (start + audio_duration + 5s) <= video_length
        max_start = max(0, video_len - duration - 5)
        start_time = random.uniform(0, max_start)
        
        output_filename = f"temp_background_{timestamp}.mp4"
        output_path = os.path.join("output", "videos", output_filename)
        
        # Trim using FFmpeg (fast seeking -ss before -i)
        # Scale and crop to 1080x1920 (center crop)
        # scale=1920:1080,crop=1080:1920:(1920-1080)/2:0
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-t", str(duration + 1), # +1s buffer
            "-i", bg_path,
            "-vf", "scale=-2:1920,crop=1080:1920:(iw-1080)/2:(ih-1920)/2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            output_path
        ]
        
        logger.info(f"Trimming background video: {bg_video}")
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg crop failed:\n{result.stderr.decode()}")
        
        return output_path

    def _get_video_duration(self, path: str):
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return float(res.stdout.strip())
