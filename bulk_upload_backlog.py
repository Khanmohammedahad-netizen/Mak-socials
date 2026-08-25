import os
import json
import time
import argparse
from datetime import datetime
from engine.uploader.youtube_uploader import YouTubeUploader
from engine.utils.logger import logger

def bulk_upload(dry_run=False, start_date="20260405_000000"):
    log_path = os.path.join("output", "run_log.json")
    if not os.path.exists(log_path):
        logger.error(f"Run log not found at {log_path}")
        return

    with open(log_path, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load run log: {e}")
            return

    # Filter for candidates
    # We look for entries after start_date that don't have a youtube_id
    candidates = []
    for entry in data:
        ts = entry.get("timestamp", "")
        if ts >= start_date and not entry.get("youtube_id"):
            candidates.append(entry)

    logger.info(f"Found {len(candidates)} videos in backlog after {start_date}")

    if dry_run:
        for c in candidates:
            logger.info(f"DRY RUN: Would upload {c.get('title')} (ID: {c.get('timestamp')})")
        return

    if not candidates:
        logger.info("Nothing to upload.")
        return

    uploader = YouTubeUploader()
    
    success_count = 0
    fail_count = 0

    for i, entry in enumerate(candidates):
        ts = entry.get("timestamp")
        title = entry.get("title", "Untitled")
        video_path = entry.get("video_path")
        thumbnail_path = entry.get("thumbnail_path")
        description = entry.get("script", "") # Use script as basis for description

        logger.info(f"[{i+1}/{len(candidates)}] Processing: {title} ({ts})")
        
        if not video_path or not os.path.exists(video_path):
            logger.warning(f"Video file missing: {video_path}. Skipping.")
            fail_count += 1
            continue

        try:
            video_id = uploader.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                thumbnail_path=thumbnail_path
            )

            if video_id:
                logger.info(f"Successfully uploaded: {video_id}")
                entry["youtube_id"] = video_id
                success_count += 1
                
                # Save log after each success to prevent data loss on crash
                with open(log_path, "w") as f:
                    json.dump(data, f, indent=2)
            else:
                logger.error(f"Failed to upload {ts}")
                fail_count += 1

        except Exception as e:
            logger.error(f"Error during bulk upload of {ts}: {e}")
            fail_count += 1

        if i < len(candidates) - 1:
            logger.info("Waiting 30 seconds before next upload...")
            time.sleep(30)

    logger.info(f"Bulk Upload Complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk upload backlog to YouTube")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    parser.add_argument("--start-date", type=str, default="20260405_000000", help="Timestamp to start from (YYYYMMDD_HHMMSS)")
    
    args = parser.parse_args()
    bulk_upload(dry_run=args.dry_run, start_date=args.start_date)
