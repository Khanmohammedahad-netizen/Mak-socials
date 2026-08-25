import os
import json
import time
import threading
import asyncio
import glob
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

# Import engine components
from engine.scheduler import ViralEngine
from engine.lib.title_optimizer import generate_optimized_title
from engine.utils.logger import logger
from src.core.config import settings
from src.dashboard.auth import require_bearer_token
from src.dashboard.money_campaigns import money_campaigns_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(money_campaigns_bp)

# Constants
OUTPUT_DIR = "output"
PUBLISHED_DIR = os.path.join(OUTPUT_DIR, "published")

# Global instances
engine = ViralEngine()
scheduler = BackgroundScheduler()
start_time = time.time()
job_id = "viral_pipeline_job"

def get_engine_status():
    jobs = scheduler.get_jobs()
    is_running = scheduler.running
    next_run = None
    if jobs:
        next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None
    
    return {
        "engine_running": is_running,
        "next_run_iso": next_run,
        "daily_quota_used": 3, 
        "daily_quota_max": 6,
        "cycle_count": 2,
        "uptime_seconds": int(time.time() - start_time)
    }

@app.route('/')
def dashboard():
    with open('MAK_Socials_Dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()
    # The token stays server-side except for this one substitution: the
    # page is only ever served on 127.0.0.1, to whoever is already sitting
    # at this machine, and needs it to call the /api/* routes it renders.
    html = html.replace('__MAK_DASHBOARD_TOKEN__', settings.mak_dashboard_token)
    return html

@app.route('/api/status', methods=['GET'])
@require_bearer_token
def status():
    return jsonify(get_engine_status())

@app.route('/api/videos')
@require_bearer_token
def list_videos():
    videos = []
    
    # Load run logs for titles and metadata
    run_logs = {}
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
                for entry in logs:
                    ts = entry.get('timestamp', '')
                    # Normalize timestamp
                    clean_ts = ts.split('T')[0].replace('-', '') + "_" + ts.split('T')[1].replace(':', '')[:6] if 'T' in ts else ts
                    run_logs[ts] = entry
                    if clean_ts != ts:
                        run_logs[clean_ts] = entry
        except Exception as e:
            logger.error(f"Error loading logs: {e}")

    # Scan published directory
    if os.path.exists(PUBLISHED_DIR):
        for date_dir in os.listdir(PUBLISHED_DIR):
            date_path = os.path.join(PUBLISHED_DIR, date_dir)
            if os.path.isdir(date_path):
                for vid_dir in os.listdir(date_path):
                    vid_path = os.path.join(date_path, vid_dir)
                    if os.path.isdir(vid_path):
                        # Find video file
                        video_file = next((f for f in os.listdir(vid_path) if f.endswith('.mp4')), None)
                        if video_file:
                            video_id = vid_dir
                            # Try to get metadata from logs
                            log_entry = run_logs.get(video_id, {})
                            title = log_entry.get('title', video_file.replace('.mp4', '').replace('_', ' '))
                            is_ai = log_entry.get('is_ai_title', False)
                            
                            # Determine platforms successfully published to
                            platforms = []
                            if log_entry.get('youtube_id'): platforms.append('yt')
                            if log_entry.get('snap_emailed'): platforms.append('sc')
                            # Note: IG is skipped for now as per scheduler.py
                            
                            videos.append({
                                "id": video_id,
                                "title": title,
                                "is_ai_title": is_ai,
                                "date": date_dir,
                                "duration": f"0:{int(log_entry.get('duration_seconds', 50))}" if log_entry.get('duration_seconds') else "0:50",
                                "status": "published" if log_entry.get('success') else ("failed" if log_entry.get('errors') else "draft"),
                                "platforms_published": platforms,
                                "yt_id": log_entry.get('youtube_id'),
                                "url": f"/output/published/{date_dir}/{vid_dir}/{video_file}",
                                "thumbnail": f"/output/thumbnails/{video_id}.jpg" if os.path.exists(f"output/thumbnails/{video_id}.jpg") else None
                            })
    
    # Sort by ID descending (newest first)
    videos.sort(key=lambda x: x['id'], reverse=True)
    return jsonify(videos)

@app.route('/api/regenerate-title', methods=['POST'])
@require_bearer_token
def regenerate_title():
    data = request.json
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({"success": False, "error": "No video_id provided"}), 400
        
    log_path = os.path.join(OUTPUT_DIR, "run_log.json")
    if not os.path.exists(log_path):
        return jsonify({"success": False, "error": "Run log not found"}), 404
        
    try:
        with open(log_path, "r") as f:
            logs = json.load(f)
            
        entry_found = None
        for entry in logs:
            if video_id in str(entry.get('timestamp', '')):
                entry_found = entry
                break
        
        if not entry_found:
            return jsonify({"success": False, "error": "Video record not found in logs"}), 404
            
        script = entry_found.get('script')
        if not script:
            return jsonify({"success": False, "error": "No script found for this video"}), 400
            
        new_title = generate_optimized_title(script)
        entry_found['title'] = new_title
        entry_found['is_ai_title'] = True
        
        with open(log_path, "w") as f:
            json.dump(logs, f, indent=2)
            
        return jsonify({"success": True, "new_title": new_title})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
@require_bearer_token
def get_logs():
    limit = request.args.get('limit', default=50, type=int)
    log_files = glob.glob(os.path.join("output", "logs", "*.log"))
    if not log_files:
        return jsonify([])
    
    latest_log = max(log_files, key=os.path.getmtime)
    
    lines = []
    with open(latest_log, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        for line in all_lines[-limit:]:
            parts = line.split(" - ")
            if len(parts) >= 3:
                lines.append({
                    "time": parts[0].split(" ")[1],
                    "level": parts[1].lower(),
                    "msg": " - ".join(parts[2:]).strip()
                })
    
    return jsonify(lines[::-1])

@app.route('/api/run-now', methods=['POST'])
@require_bearer_token
def run_now():
    def background_run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(engine.run_pipeline())
    
    thread = threading.Thread(target=background_run)
    thread.start()
    return jsonify({"started": True, "message": "Pipeline triggered"})

@app.route('/api/engine/toggle', methods=['POST'])
@require_bearer_token
def toggle_engine():
    # Toggle logic...
    return jsonify({"success": True})

if __name__ == "__main__":
    if not settings.enable_legacy_autopublish:
        logger.info(
            f"job '{job_id}' disabled by flag "
            "(ENABLE_LEGACY_AUTOPUBLISH=False) - not registered."
        )
    elif engine.config['scheduling'].get('enabled', True):
        interval = engine.config['scheduling']['interval_hours']
        scheduler.add_job(
            lambda: asyncio.run(engine.run_pipeline()),
            'interval',
            hours=interval,
            id=job_id
        )
        scheduler.start()
        logger.info(f"Background scheduler started (interval: {interval}h)")

    app.run(host="127.0.0.1", port=5050, debug=False)
