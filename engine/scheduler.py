import os
import time
import json
import yaml
import shutil
import asyncio
import traceback
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from engine.utils.logger import logger
from engine.utils.background_manager import BackgroundManager
from engine.utils.music_mixer import MusicMixer
from engine.script_generator import ScriptGenerator
from engine.tts_engine import TTSEngine, ScriptTooShortError
from engine.subtitle_generator import SubtitleGenerator
from engine.video_composer import VideoComposer, CompositionError
from engine.thumbnail_generator import ThumbnailGenerator
from engine.lib.title_optimizer import generate_optimized_title
from engine.uploader.youtube_uploader import YouTubeUploader
from engine.uploader.instagram_uploader import InstagramUploader
from engine.uploader.snapchat_emailer import SnapchatEmailer
from src.core.config import settings

class ViralEngine:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.script_gen = ScriptGenerator(config_path)
        self.tts_engine = TTSEngine(config_path)
        self.sub_gen = SubtitleGenerator(config_path)
        self.bg_manager = BackgroundManager()  # defaults to "assets/backgrounds"
        self.music_mixer = MusicMixer()          # defaults to "assets/music"
        self.composer = VideoComposer(config_path)
        self.thumb_gen = ThumbnailGenerator(config_path)
        
        self.yt_uploader = YouTubeUploader(config_path)
        self.ig_uploader = InstagramUploader(config_path)
        self.sc_emailer = SnapchatEmailer(config_path)
        
        self.run_log_path = os.path.join("output", "run_log.json")

    async def run_pipeline(self):
        """Executes the full content generation and publishing pipeline."""
        start_time = datetime.now()
        logger.info(f"=== Starting Pipeline Run: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        run_info = {
            "timestamp": start_time.isoformat(),
            "success": False,
            "errors": []
        }
        
        try:
            # 1. Script Generation
            script_data = self.script_gen.generate()
            
            # 1b. AI Title Optimization
            optimized_title = generate_optimized_title(script_data['script'], self.config_path)
            script_data['title'] = optimized_title
            script_data['is_ai_title'] = True
            
            run_info.update(script_data)
            
            # 2. TTS Generation (with retry on ScriptTooShort)
            audio_data = None
            for attempt in range(5):
                try:
                    audio_data = await self.tts_engine.generate_audio(script_data['script'], script_data['timestamp'])
                    break
                except ScriptTooShortError:
                    logger.warning("Script too short for minimum duration. Regenerating...")
                    script_data = self.script_gen.generate()
            
            if not audio_data:
                raise Exception("Failed to generate valid length audio after 5 attempts.")
                
            run_info.update(audio_data)
            
            # 3. Subtitle Generation (ASS)
            sub_data = self.sub_gen.generate_ass(audio_data['audio_path'], script_data['timestamp'])
            run_info.update(sub_data)
            
            # 4. Prepare Composition Assets
            bg_path = self.bg_manager.select_and_trim(audio_data['duration_seconds'], script_data['timestamp'])
            mixed_audio_path = self.music_mixer.mix_audio(
                audio_data['audio_path'], 
                audio_data['duration_seconds'], 
                script_data['timestamp'],
                self.config['music']['volume_percent']
            )
            
            # 5. Video Composition (ASS Burn-in)
            video_path = self.composer.compose(
                bg_video_path=bg_path,
                mixed_audio_path=mixed_audio_path,
                ass_path=sub_data["ass_path"],
                audio_duration=audio_data["duration_seconds"],
                timestamp=script_data['timestamp'],
                title=script_data['title']
            )
            run_info["video_path"] = video_path
            
            # 5. Thumbnail Generation
            thumb_path = self.thumb_gen.generate_thumbnail(video_path, script_data['title'], script_data['timestamp'])
            run_info["thumbnail_path"] = thumb_path
            
            # 6. Publishing
            # YouTube
            if self.config['scheduling']['platforms']['youtube']:
                try:
                    yt_id = self.yt_uploader.upload_video(
                        video_path, 
                        script_data['title'], 
                        self.config['youtube']['description_template'].format(title=script_data['title']),
                        thumb_path
                    )
                    run_info["youtube_id"] = yt_id
                    if not yt_id:
                        run_info["errors"].append("YouTube upload returned None (check logs for quota/token issues)")
                except Exception as e:
                    logger.error(f"YouTube upload exception: {e}")
                    run_info["errors"].append(f"YouTube upload exception: {str(e)}")
                    run_info["youtube_id"] = None
            
            # Short sleep to avoid rate limits
            time.sleep(30)
            
            # Instagram (IG needs public URL, this usually requires an intermediate host or local tunnel)
            # For now, we log that manual/tunnel step is needed or IG is skipped.
            if self.config['scheduling']['platforms']['instagram']:
                # Note: IG requires a public URL. In production, you'd upload to S3/B2 first.
                logger.info("Instagram upload requires a public video URL. See README for hosting setup.")
                # ig_id = self.ig_uploader.upload_reel(PUBLIC_URL, caption)
                pass
            
            # Snapchat Email
            if self.config['scheduling']['platforms']['snapchat_email']:
                emailed = self.sc_emailer.send_video(video_path, script_data['title'], script_data['script'])
                run_info["snap_emailed"] = emailed
                
            # 7. Post-Publishing: Move to published
            pub_date = datetime.now().strftime("%Y-%m-%d")
            pub_dir = os.path.join("output", "published", pub_date, script_data['timestamp'])
            os.makedirs(pub_dir, exist_ok=True)
            
            final_video_dest = os.path.join(pub_dir, os.path.basename(video_path))
            
            # Use retry loop for Windows file locking issues
            moved = False
            for i in range(5):
                try:
                    shutil.move(video_path, final_video_dest)
                    moved = True
                    break
                except PermissionError:
                    logger.warning(f"File locked, retrying move ({i+1}/5)...")
                    time.sleep(2)
            
            if not moved:
                shutil.copy2(video_path, final_video_dest) # Fallback to copy if move fails
                logger.info("Fallbacked to copy video after locking issues.")
            
            run_info["video_path"] = final_video_dest
            
            run_info["success"] = True
            logger.info(f"=== Pipeline Run Successful! Video: {final_video_dest} ===")
            
        except Exception as e:
            err_msg = f"Pipeline Error: {str(e)}"
            logger.error(err_msg)
            logger.error(traceback.format_exc())
            run_info["errors"].append(err_msg)
            # Optional: send error email to self
            
        finally:
            self._save_run_log(run_info)

    def _save_run_log(self, info):
        logs = []
        if os.path.exists(self.run_log_path):
            with open(self.run_log_path, "r") as f:
                try: logs = json.load(f)
                except: logs = []
        
        logs.append(info)
        with open(self.run_log_path, "w") as f:
            json.dump(logs, f, indent=2)

def start_scheduler():
    if not settings.enable_legacy_autopublish:
        logger.info(
            "job 'legacy_autopublish' disabled by flag "
            "(ENABLE_LEGACY_AUTOPUBLISH=False) - not registered."
        )
        return

    engine = ViralEngine()
    scheduler = BackgroundScheduler()

    interval = engine.config['scheduling']['interval_hours']
    logger.info(f"Starting scheduler: Running every {interval} hours.")

    def job():
        asyncio.run(engine.run_pipeline())

    scheduler.add_job(job, 'interval', hours=interval, id="legacy_autopublish")
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    # Test single run
    engine = ViralEngine()
    asyncio.run(engine.run_pipeline())
