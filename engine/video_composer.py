import os
import subprocess
import yaml
import shutil
from engine.utils.logger import logger

class CompositionError(Exception):
    pass

def get_ffmpeg_path() -> str:
    path = shutil.which('ffmpeg')
    if path:
        return path
    # Common Windows install locations
    candidates = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\tools\ffmpeg\bin\ffmpeg.exe',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise RuntimeError(
        "FFmpeg not found. Make sure ffmpeg is installed "
        "and in your system PATH."
    )

FFMPEG = get_ffmpeg_path()

class VideoComposer:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = os.path.join("output", "videos")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def compose(self, bg_video_path: str, mixed_audio_path: str, ass_path: str, audio_duration: float, timestamp: str, title: str) -> str:
        """Orchestrates the final video composition using ASS subtitles."""
        logger.info(f"Starting video composition for: {title}")
        
        # Build final output path
        title_slug = "".join([c if c.isalnum() else "_" for c in title])[:30]
        final_output_path = os.path.join(self.output_dir, f"{timestamp}_{title_slug}.mp4")
        
        # Sanitize paths — forward slashes only for FFmpeg
        bg = bg_video_path.replace('\\', '/')
        audio = mixed_audio_path.replace('\\', '/')
        # Use abspath for subtitles to ensure FFmpeg finds it
        subs = os.path.abspath(ass_path).replace('\\', '/')
        # FFmpeg on Windows needs the colon escaped in the subtitles filter: subtitles='C\:/path/to/file.ass'
        subs = subs.replace(':', r'\:')
        out = final_output_path.replace('\\', '/')
        
        # Build the FFmpeg command as a list
        cmd = [
            FFMPEG, '-y',
            '-i', bg,
            '-i', audio,
            '-vf', f"subtitles='{subs}'",
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(round(audio_duration, 3)),
            out
        ]
        
        try:
            logger.info(f"Running final FFmpeg render using {FFMPEG}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg path used: {FFMPEG}")
                logger.error(f"FFmpeg stderr:\n{result.stderr[-3000:]}")
                raise CompositionError(
                    f"FFmpeg render failed (exit {result.returncode}):\n"
                    f"{result.stderr[-1500:]}"
                )
            
            # Step 4: Quality Validation
            self._validate_output(final_output_path, audio_duration)
            
            # Step 5: Cleanup
            temp_files = [
                bg_video_path,
                mixed_audio_path,
            ]
            self._cleanup(temp_files)
            
            logger.info(f"Composition successful: {final_output_path}")
            return final_output_path
            
        except Exception as e:
            logger.error(f"Composition failed: {e}")
            raise CompositionError(f"Composition failed: {e}")

    def _validate_output(self, path: str, expected_duration: float):
        if not os.path.exists(path):
            raise CompositionError("Output file does not exist.")
            
        size = os.path.getsize(path) / (1024 * 1024) # MB
        if size < 2.0:
            logger.warning(f"Output file size is very small: {size:.2f}MB")
            
        # Check duration
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        actual_duration = float(res.stdout.strip())
        
        if abs(actual_duration - expected_duration) > 2.0:
            logger.warning(f"Duration mismatch: Expected {expected_duration}s, got {actual_duration}s")
            
    def _cleanup(self, paths: list):
        for p in paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
                    logger.debug(f"Cleaned up temp file: {p}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {p}: {e}")

if __name__ == "__main__":
    # Test block
    # composer = VideoComposer()
    pass
