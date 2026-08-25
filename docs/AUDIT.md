# MAK Socials — Read-Only Audit

Audit date: 2026-08-25
Scope: `C:\Users\ahad\MAK Socials`
Method: static inspection only. No pipeline stage was executed, no file other than this one was modified, no git state was changed.

---

## 0. Executive Summary

`C:\Users\ahad\MAK Socials` **is** a real, working faceless-Shorts pipeline (Ollama script → edge-tts → Whisper word-level captions → FFmpeg burn-in → YouTube/Instagram/Snapchat). It is small (~2,700 lines of first-party Python across ~20 files), it has run for real (88 logged pipeline runs, 66 successful, 64 YouTube uploads between 2026-03-29 and 2026-04-12, plus one failed attempt on 2026-07-09), and it currently exists **completely outside version control** — see Section 13. It has been dormant since 2026-07-09 (its YouTube refresh token is also currently invalid, per that day's log).

---

## 1. FILE TREE

Depth 4, excluding `venv311/`, `__pycache__/`, `.git/`, `data/` (does not exist), `output/` (excluded per instructions — it holds ~40 dated run subfolders, real videos/logs, see Section 10). `node_modules/` and `dashboard/frontend/.next/` are also collapsed below (build artifacts, not source) but their presence is noted.

```
MAK Socials/
├── .env                                    (12 lines — real credentials, see §9)
├── README.md                               (48 lines)
├── main.py                                 (52 lines)  — CLI entry point
├── dashboard_api.py                        (206 lines) — Flask API, port 5050
├── bulk_upload_backlog.py                  (96 lines)  — standalone backlog uploader CLI
├── setup.py                                (73 lines)  — first-run environment setup
├── requirements.txt                        (15 lines)
├── MAK_Socials_Dashboard.html              (1237 lines) — static dashboard UI served by Flask
│
├── assets/
│   ├── backgrounds/
│   │   └── 4.mp4                           (2.29 GB — the ONLY background clip present)
│   ├── music/                              (4 .mp3 tracks, ~30 MB total, no licence file)
│   └── fonts/
│       ├── Montserrat-Bold.ttf             (used by thumbnail_generator.py)
│       └── Montserrat/                     (full variable-font family + OFL.txt licence)
│
├── config/
│   ├── config.yaml                         (87 lines — pipeline config, see §6c/§8)
│   └── credentials/
│       ├── youtube_client_secret.json      (Google OAuth client, 407 B)
│       └── youtube_token.json              (pickled OAuth creds despite .json name, 1144 B)
│
├── database/
│   └── videos.json                         (9 lines, 1 stub test row — see §7)
│
├── engine/
│   ├── __init__.py
│   ├── scheduler.py                        (212 lines) — ViralEngine orchestrator + APScheduler
│   ├── script_generator.py                 (230 lines) — Ollama script + title generation
│   ├── tts_engine.py                       (101 lines) — edge-tts wrapper
│   ├── subtitle_generator.py               (175 lines) — Whisper → ASS captions
│   ├── video_composer.py                   (141 lines) — FFmpeg render
│   ├── thumbnail_generator.py              (124 lines) — Pillow thumbnail
│   ├── lib/
│   │   └── title_optimizer.py              (61 lines) — 2nd Ollama call for click-title
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── background_manager.py           (61 lines) — clip select/crop
│   │   ├── music_mixer.py                  (44 lines) — bg-music mix
│   │   └── logger.py                       (53 lines) — colorlog + file logger
│   └── uploader/
│       ├── __init__.py
│       ├── youtube_uploader.py             (185 lines) — YouTube Data API v3
│       ├── instagram_uploader.py           (101 lines) — IG Graph API (not wired up, see §5)
│       └── snapchat_emailer.py             (90 lines)  — SMTP email, not a real upload
│
├── dashboard/
│   ├── backend/                            — DEAD: only package-lock.json + node_modules,
│   │                                          no package.json, no source file exists
│   └── frontend/                           — unmodified `create-next-app` scaffold
│       ├── .git/                           — its OWN separate nested repo, 1 commit
│       │                                     ("Initial commit from Create Next App")
│       ├── node_modules/                   (collapsed, build dependency tree)
│       ├── .next/                          (collapsed, dev build cache)
│       ├── src/app/{page.tsx,layout.tsx,globals.css}  — stock Next.js boilerplate, unedited
│       ├── package.json / package-lock.json (6842 lines)
│       └── AGENTS.md, CLAUDE.md, README.md — stock scaffold docs
│
├── n8n/                                    — EMPTY directory, no workflow files
│
├── output/                                 (excluded per audit scope — real run artifacts)
└── venv311/                                (excluded — Python 3.11 virtualenv, ~180 packages)
```

### 10 largest files (by size, whole tree, excluding venv311/node_modules/.next)

| # | File | Size |
|---|------|------|
| 1 | `assets/backgrounds/4.mp4` | 2.29 GB |
| 2 | `assets/music/Fire In The Sky - Alex Jones & Xander Jones.mp3` | 10.3 MB |
| 3 | `assets/music/Ancient Civilisations - Alex Jones & Xander Jones.mp3` | 7.7 MB |
| 4 | `assets/music/Stake Out - Alex Jones & Xander Jones.mp3` | 7.0 MB |
| 5 | `assets/music/Conspiracy Theory - Rod Kim.mp3` | 3.7 MB |
| 6 | `assets/fonts/Montserrat/Montserrat-Italic-VariableFont_wght.ttf` | 701 KB |
| 7 | `assets/fonts/Montserrat/Montserrat-VariableFont_wght.ttf` | 689 KB |
| 8 | `dashboard/frontend/package-lock.json` | 236 KB |
| 9 | `assets/fonts/Montserrat/static/Montserrat-ExtraBoldItalic.ttf` | 349 KB |
| 10 | `assets/fonts/Montserrat/static/Montserrat-BlackItalic.ttf` | 348 KB |

**10 largest files by line count (code/text only):**

| # | File | Lines |
|---|------|-------|
| 1 | `dashboard/frontend/package-lock.json` | 6,842 |
| 2 | `dashboard/backend/package-lock.json` | 1,559 |
| 3 | `MAK_Socials_Dashboard.html` | 1,237 |
| 4 | `engine/script_generator.py` | 230 |
| 5 | `engine/scheduler.py` | 212 |
| 6 | `dashboard_api.py` | 206 |
| 7 | `engine/uploader/youtube_uploader.py` | 185 |
| 8 | `engine/subtitle_generator.py` | 175 |
| 9 | `engine/video_composer.py` | 141 |
| 10 | `engine/thumbnail_generator.py` | 124 |

Total first-party code/text (excluding binaries, venv, node_modules): ~50 files. First-party Python: ~2,700 lines.

---

## 2. DEPENDENCIES

`requirements.txt` (15 entries, mostly unpinned):

| Package | Pinned version | Installed (venv311) | Imported in project code? |
|---|---|---|---|
| `edge-tts` | — | 7.2.8 | Yes — `engine/tts_engine.py` |
| `openai-whisper` | — | 20250625 | Yes — `engine/subtitle_generator.py` (`import whisper`) |
| `moviepy` | `==1.0.3` | 1.0.3 | **No** — not imported anywhere; all video work goes through raw `subprocess`/FFmpeg |
| `ffmpeg-python` | — | 0.2.0 | **No** — not imported; FFmpeg is invoked via `subprocess` calls with hand-built command lists (see §6d) |
| `ollama` | — | 0.6.1 | Yes — `engine/script_generator.py`, `engine/lib/title_optimizer.py` |
| `apscheduler` | — | 3.11.2 | Yes — `engine/scheduler.py`, `dashboard_api.py` |
| `google-api-python-client` | — | 2.193.0 | Yes — `engine/uploader/youtube_uploader.py` |
| `google-auth-oauthlib` | — | 1.3.0 | Yes — `engine/uploader/youtube_uploader.py` |
| `requests` | — | 2.33.0 | Yes — `engine/uploader/instagram_uploader.py`, `setup.py` |
| `Pillow` | — | 12.1.1 | Yes — `engine/thumbnail_generator.py` (`import PIL`) |
| `PyYAML` | — | 6.0.3 | Yes — every `engine/*.py` module (`import yaml`) |
| `python-dotenv` | — | 1.2.2 | Yes — `engine/uploader/instagram_uploader.py`, `engine/uploader/snapchat_emailer.py` |
| `colorlog` | — | 6.10.1 | Yes — `engine/utils/logger.py` |
| `pydub` | — | 0.25.1 | Yes — `engine/tts_engine.py` |
| `numpy` | — | 2.4.3 | **No** — not directly imported by any first-party file (present only as a transitive dependency of whisper/torch/pydub) |

**Flagged unused (declared, never directly imported): `moviepy`, `ffmpeg-python`, `numpy`.**
`flask` and `flask_cors` are imported by `dashboard_api.py` but are **missing from `requirements.txt` entirely** — the dashboard API would not install cleanly from `requirements.txt` alone. `smtplib`, `email`, `pickle`, `argparse`, etc. are stdlib and correctly not listed.

No `pyproject.toml` exists in this project (there is one inside `dashboard/frontend`, but that's an unrelated Next.js scaffold with no Python content).

---

## 3. ENTRY POINTS

| Kind | Location | Detail |
|---|---|---|
| `if __name__ == "__main__"` | `main.py:51` | Primary CLI (`argparse`) |
| `if __name__ == "__main__"` | `dashboard_api.py:194` | Flask app launcher |
| `if __name__ == "__main__"` | `bulk_upload_backlog.py:90` | Standalone backlog-uploader CLI |
| `if __name__ == "__main__"` | `setup.py:72` | Setup/env-check script |
| `if __name__ == "__main__"` | `engine/scheduler.py:209` | Direct single-run test harness (imports itself as script) |
| `if __name__ == "__main__"` | `engine/script_generator.py:227` | Module self-test (prints one generated script) |
| `if __name__ == "__main__"` | `engine/tts_engine.py:91` | Module self-test |
| `if __name__ == "__main__"` | `engine/subtitle_generator.py:172` | Module self-test (body commented out) |
| `if __name__ == "__main__"` | `engine/video_composer.py:138` | Module self-test (body is `pass`) |
| `if __name__ == "__main__"` | `engine/thumbnail_generator.py:121` | Module self-test (body commented out) |
| `if __name__ == "__main__"` | `engine/uploader/youtube_uploader.py:182` | Module self-test (body commented out) |
| `if __name__ == "__main__"` | `engine/uploader/instagram_uploader.py:98` | Module self-test (body commented out) |
| `if __name__ == "__main__"` | `engine/uploader/snapchat_emailer.py:87` | Module self-test (body commented out) |

**CLI flags** (`main.py:12-24`): `--run-now`, `--schedule`, `--test`, `--setup`.

**APScheduler job registrations:**
- `engine/scheduler.py:200` — `scheduler.add_job(job, 'interval', hours=interval)` inside `start_scheduler()`, no explicit `id`, interval pulled from `config.yaml → scheduling.interval_hours` (4h).
- `dashboard_api.py:197-202` — a **second, independent** `BackgroundScheduler` instance registers the same job (`id="viral_pipeline_job"`, interval hours) when `dashboard_api.py` is run directly. If both `main.py --schedule` and `dashboard_api.py` are run at the same time, **the pipeline fires from two unrelated schedulers simultaneously** — no shared lock/coordination exists between them.

No Celery, cron, or Windows Task Scheduler integration exists anywhere in the repo.

---

## 4. PIPELINE TRACE — one Short, end to end

Entry: `python main.py --run-now` → `main.py:37-38` → `ViralEngine().run_pipeline()`.

1. **Trigger** — `main.py:37` (`--run-now`) or `engine/scheduler.py:200` (APScheduler interval) or `dashboard_api.py:178-187` (`POST /api/run-now`, spawns a thread). All three converge on `ViralEngine.run_pipeline()` in `engine/scheduler.py:43`.
2. **Script/content source** — `engine/scheduler.py:56` calls `self.script_gen.generate()` → `engine/script_generator.py:94`. Picks a random hardcoded premise from a 51-item in-code list (`script_generator.py:24-76`) and a random `sub_variant` from `config.yaml:3-8`, then calls Ollama (`script_generator.py:161`, model from `config.yaml:43` = `llama3.2`, `http://localhost:11434`).
3. **Title (AI)** — same Ollama call pattern, `script_generator.py:198` generates a title; overridden again immediately after by `engine/scheduler.py:59` → `engine/lib/title_optimizer.py:59` (`generate_optimized_title`), a second, separate Ollama chat call.
4. **TTS** — `engine/scheduler.py:69` → `engine/tts_engine.py:27` `TTSEngine.generate_audio()`. Randomly picks one of 3 hardcoded edge-tts voices (`tts_engine.py:21-25`, note: this list is NOT read from `config.yaml`, which separately defines `tts.voice`/`tts.backup_voice` that are never used). Calls `edge_tts.Communicate(...).save()` (`tts_engine.py:39-46`).
5. **Audio post-process / length gate** — `tts_engine.py:61` `_post_process_audio()`. If < 38.0s (hardcoded, not `config.yaml`'s `duration_min: 45`), raises `ScriptTooShortError`, caught at `engine/scheduler.py:71-73`, which regenerates the script and retries (up to 5 attempts, `scheduler.py:67`). Trims to 57s if over `config['video']['duration_max']` (`tts_engine.py:71-74`). Normalizes to ‑18 dBFS (`tts_engine.py:77-78`).
6. **Transcription (word-level captions)** — `engine/scheduler.py:81` → `engine/subtitle_generator.py:21` `generate_ass()`. Runs `self.model.transcribe(audio_path, word_timestamps=True, language='en')` at `subtitle_generator.py:26-30` (Whisper model loaded once at `subtitle_generator.py:18`, size **"base"**). Extracts per-word timestamps (`subtitle_generator.py:34-40`), chunks them into 3-word caption groups (`subtitle_generator.py:45-104`), writes an `.ass` file with hardcoded 1080×1920 `PlayResX/Y` (`subtitle_generator.py:133-134`) and a hardcoded style line (`subtitle_generator.py:139`) — **`config.yaml`'s entire `caption_style` block (font, size, color, highlight_current_word, etc., `config.yaml:16-26`) is defined but never read by this code.**
7. **Asset selection (background clip)** — `engine/scheduler.py:85` → `engine/utils/background_manager.py:13` `select_and_trim()`. Picks a random `.mp4` from `assets/backgrounds/` (only one file, `4.mp4`, currently present — "random" is a no-op today), picks a random start offset, and crops/scales to 1080×1920 via FFmpeg (`background_manager.py:38-46`).
8. **Music mix** — `engine/scheduler.py:86-91` → `engine/utils/music_mixer.py:12` `mix_audio()`. Picks a random `.mp3` from `assets/music/`, mixes with TTS via FFmpeg `amix` filter at `config.yaml:38`'s `volume_percent` (12%).
9. **Caption burn-in / final render (FFmpeg)** — `engine/scheduler.py:94-101` → `engine/video_composer.py:40` `compose()`. Builds and runs the FFmpeg command at `video_composer.py:58-73` (full command printed in §6d). Validates output exists and duration matches (`video_composer.py:110-127`), deletes temp inputs (`video_composer.py:129-136`).
10. **Thumbnail** — `engine/scheduler.py:105` → `engine/thumbnail_generator.py:24` `generate_thumbnail()`. Extracts a frame at t=2s via FFmpeg (`thumbnail_generator.py:30-34`), overlays title text with Pillow.
11. **Publish — YouTube** — `engine/scheduler.py:110-124` → `engine/uploader/youtube_uploader.py:70` `upload_video()`. OAuth via pickled token (`youtube_uploader.py:20-68`), resumable upload with retry/backoff (`youtube_uploader.py:130-170`), sets thumbnail (`youtube_uploader.py:172-181`).
12. **Publish — Instagram** — `engine/scheduler.py:131-135` — **the actual upload call is commented out** (`# ig_id = self.ig_uploader.upload_reel(...)`, `scheduler.py:134`); only a log line fires. The IG uploader class exists and is fully implemented (`engine/uploader/instagram_uploader.py`) but is never invoked by the live pipeline because it requires a publicly reachable video URL that nothing in this repo produces.
13. **Publish — Snapchat** — `engine/scheduler.py:138-140` → `engine/uploader/snapchat_emailer.py:23` `send_video()`. Not a real Snapchat API integration — it emails the finished video (or a path reference if >25 MB) to a human, who is expected to post it to Snapchat Spotlight manually (`snapchat_emailer.py:36-51`).
14. **Post-publish move** — `engine/scheduler.py:142-164` moves the final video into `output/published/<date>/<timestamp>/`, with a Windows-file-lock retry loop (`scheduler.py:150-162`).
15. **Run log** — `engine/scheduler.py:179` `_save_run_log()` appends the full run record (including full script text) to `output/run_log.json`.

This pipeline is real and has executed successfully 66/88 times historically (see §10).

---

## 5. INTEGRATION INVENTORY

| Integration | Module | Model/voice/params | Auth | Credential storage | Error handling | Quota handling |
|---|---|---|---|---|---|---|
| **Ollama** | `engine/script_generator.py`, `engine/lib/title_optimizer.py` | model `llama3.2` (`config.yaml:43`), temp 0.85/0.7, `num_predict` 800 (script) | none (local HTTP, `http://localhost:11434`) | n/a | try/except around `generate()`, re-raises (`script_generator.py:223-225`); title path falls back to a truncated string on failure (`title_optimizer.py:52-57`) | none — no rate limiting, no queue |
| **edge-tts** | `engine/tts_engine.py` | 3 hardcoded voices (`ChristopherNeural`/`GuyNeural`/`EricNeural`), `rate`/`pitch`/`volume` from `config.yaml:32-34` | Microsoft's free edge-tts endpoint, no key | n/a | no explicit try/except around `communicate.save()` — an edge-tts failure propagates uncaught to the top-level pipeline handler | none (edge-tts is unofficial/free; no quota logic) |
| **Whisper (openai-whisper)** | `engine/subtitle_generator.py` | model **"base"**, `word_timestamps=True`, `language='en'` | n/a, local | n/a | none around `self.model.transcribe()` itself — failures bubble to `scheduler.py`'s outer try/except | n/a |
| **FFmpeg** | `engine/video_composer.py`, `engine/utils/background_manager.py`, `engine/utils/music_mixer.py`, `engine/thumbnail_generator.py` | see §6d for exact commands | n/a (local binary) | n/a | `video_composer.py` checks return code and logs stderr (`video_composer.py:85-91`); `background_manager.py` raises `RuntimeError` on failure; `music_mixer.py` uses `check=True` (raises `CalledProcessError`); `thumbnail_generator.py` uses `check=True` | n/a |
| **YouTube Data API v3** | `engine/uploader/youtube_uploader.py` | category `22`, privacy `public` (`config.yaml:55-56`) | OAuth2 installed-app flow, scopes `youtube.upload` + `youtube.force-ssl` | `config/credentials/youtube_client_secret.json` (client secret) + `config/credentials/youtube_token.json` (**pickled** `Credentials` object, despite the `.json` extension) | retry with exponential backoff on 5xx (`youtube_uploader.py:130-169`); explicit handling for `quotaExceeded` and `limitExceeded` 403s (returns `None`, does not crash) | explicit — detects `quotaExceeded`/`limitExceeded` and stops retrying |
| **Instagram** | `engine/uploader/instagram_uploader.py` | Graph API v18.0, `REELS` media type | Long-lived access token via env vars | `.env`: `IG_USER_ID`, `IG_ACCESS_TOKEN` (both currently **blank** in `.env`) | try/except around requests, polls container status up to 120s (`instagram_uploader.py:72-96`) | none explicit | 
| **Snapchat** | `engine/uploader/snapchat_emailer.py` | **not an API integration** — SMTP email via Gmail (`smtp.gmail.com:465`) with the finished video as attachment, meant for a human to post manually to Spotlight | Gmail SMTP login | `.env`: `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD` (both **populated with real-looking values**, see §9) | on send failure, writes a `.txt` stub to `output/pending_emails/` (`snapchat_emailer.py:80-84`) | n/a |
| **n8n** | — | **not present** — `n8n/` directory exists and is completely empty, no workflow JSON, no references to n8n anywhere in code |
| **moviepy / ffmpeg-python** | — | **not present** — declared in `requirements.txt`, never imported (§2) |
| **Browser automation (Selenium/Playwright)** | — | **not present anywhere in the codebase** (see §6b) |

---

## 6. CRITICAL CHECKS

### a) Whisper — word_timestamps and model size (MOST IMPORTANT QUESTION)

**Yes.** `engine/subtitle_generator.py:26-30`:
```python
result = self.model.transcribe(
    audio_path,
    word_timestamps=True,
    language='en'
)
```
Implementation: **`openai-whisper`** (`import whisper`, `engine/subtitle_generator.py:2`; confirmed installed as `openai_whisper-20250625` in `venv311`), **not** `faster-whisper`. Model size: **`"base"`**, loaded once per `SubtitleGenerator` instance at `engine/subtitle_generator.py:18` (`whisper.load_model("base")`). Per-word timestamps are then extracted from `result["segments"][*]["words"]` (`subtitle_generator.py:34-40`) and used to build the burned-in ASS captions. This is functioning as designed and is the one piece of the pipeline most load-bearing for the "high-retention word-by-word captions" claim in the README — it is correctly implemented.

### b) Instagram/Snapchat browser automation

**Not present.** Grepped the entire tree (excluding third-party packages) for `selenium`, `playwright`, `undetected_chromedriver`, `webdriver` — zero matches in first-party code. Instagram uses the official Graph API (`engine/uploader/instagram_uploader.py`); Snapchat is not automated at all — it emails the video to a human (`engine/uploader/snapchat_emailer.py`). **No CRITICAL RISK of this kind exists.**

### c) Renderer resolution/fps

Output is **1080×1920**, hardcoded (not read from config) in `engine/utils/background_manager.py:43`:
```python
"-vf", "scale=-2:1920,crop=1080:1920:(iw-1080)/2:(ih-1920)/2",
```
`config.yaml:11` also declares `resolution: "1080x1920"` but **this config value is never read by any code** — it happens to match the hardcoded value today, but changing it in `config.yaml` would do nothing.

FPS is **not set anywhere** — no `-r`/`fps` flag appears in any FFmpeg command in the repo. Output framerate is simply whatever the source background clip (`4.mp4`) natively has. `config.yaml:12`'s `fps: 30` is **dead configuration**, never referenced by any Python file (confirmed via grep — zero matches for `config['video']['fps']` or similar anywhere in `engine/`).

### d) Every FFmpeg command string, with file:line

1. `engine/utils/background_manager.py:38-46` (trim/crop background clip):
```python
cmd = [
    "ffmpeg", "-y",
    "-ss", str(start_time),
    "-t", str(duration + 1),
    "-i", bg_path,
    "-vf", "scale=-2:1920,crop=1080:1920:(iw-1080)/2:(ih-1920)/2",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
    output_path
]
```
2. `engine/utils/background_manager.py:56-59` (`ffprobe`, duration probe):
```python
cmd = [
    "ffprobe", "-v", "error", "-show_entries",
    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
]
```
3. `engine/utils/music_mixer.py:24` (no-music fallback):
```python
cmd = ["ffmpeg", "-y", "-i", tts_audio_path, "-acodec", "libmp3lame", output_path]
```
4. `engine/utils/music_mixer.py:33-41` (music mix):
```python
cmd = [
    "ffmpeg", "-y",
    "-i", tts_audio_path,
    "-stream_loop", "-1", "-i", music_path,
    "-filter_complex", f"[0:a]volume=1.0[speech];[1:a]volume={vol_decimal}[music];[speech][music]amix=inputs=2:duration=first[aout]",
    "-map", "[aout]",
    "-t", str(duration),
    output_path
]
```
5. `engine/video_composer.py:58-73` (final render + caption burn-in — the main render):
```python
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
```
6. `engine/video_composer.py:119-122` (`ffprobe`, output duration validation):
```python
cmd = [
    "ffprobe", "-v", "error", "-show_entries",
    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
]
```
7. `engine/thumbnail_generator.py:30-33` (frame extraction for thumbnail):
```python
cmd = [
    "ffmpeg", "-y", "-ss", "2", "-i", video_path,
    "-vframes", "1", "-q:v", "2", frame_path
]
```

### e) Bare `except:` / `except Exception: pass`

- `setup.py:24` — bare `except:` around the FFmpeg version check.
- `setup.py:39` — bare `except:` around the Ollama reachability check.
- `engine/script_generator.py:83` — bare `except:` inside `_load_used_hooks()` (silently returns `[]` on any read/parse error).
- `engine/scheduler.py:184` — bare `except: logs = []` inside `_save_run_log()` (silently discards a corrupt run log rather than backing it up).
- `engine/thumbnail_generator.py:51` — bare `except:` around font loading, falls back to `ImageFont.load_default()`.

No literal `except Exception: pass` (with `pass` as the sole body) was found in first-party code; the five bare `except:` blocks above are the actual swallow-everything sites.

### f) Content source and rights/licensing

**Story/script text**: 100% generated at runtime by a local Ollama LLM (`llama3.2`) from a hardcoded, first-party bank of 51 short premises written directly in `engine/script_generator.py:24-76` (e.g. "My wife has been 'working late' for three months..."). This is original/AI-generated content, not scraped from Reddit or any other source — despite the README and hashtags branding it "Reddit Mystery" content, **no Reddit content is ever fetched or referenced anywhere in the code.** No licensing question applies to the script text itself.

**Background video**: a single file, `assets/backgrounds/4.mp4` (2.29 GB, appears to be gameplay footage based on naming conventions used elsewhere in the project — e.g. `config.yaml`'s `minecraftparkour` tag). **No licence file, attribution, or source record exists anywhere in the repo for this file.** Its provenance cannot be determined from static inspection.

**Background music**: 4 `.mp3` files in `assets/music/` — "Fire In The Sky", "Ancient Civilisations", "Stake Out" (all credited "Alex Jones / Xander Jones" in the filename) and "Conspiracy Theory" (credited "Rod Kim" in the filename). **No licence file or purchase/usage-rights record exists for any of them** — contrast with `assets/fonts/Montserrat/OFL.txt`, which *is* present and documents the font's Open Font License. This is a real, unaddressed gap: this content is uploaded to a monetized-intent public YouTube channel (`config.yaml:56`, `privacy: "public"`) with no rights documentation on file for either audio bed.

---

## 7. DATA LAYER

**No SQL database exists.** There is no SQLite/Postgres/MySQL file anywhere in the tree (checked for `*.db`/`*.sqlite*`, none found outside `venv311`). "Persistence" is entirely flat JSON/text files:

- `database/videos.json` — 9 lines, a single stub/test record (`id: "1774580942"`, `title: "Test Mystery"`, `status: "generated"`). This looks like a leftover test fixture, not a live table — nothing in `engine/` or `dashboard_api.py` reads from or writes to `database/videos.json`.
- `output/run_log.json` — the **actual** operational data store. A flat JSON array, one object per pipeline run (script text, title, audio/video/thumbnail paths, per-platform IDs, errors). 88 entries as of the last run (2026-07-09), file size ~930 KB. Read/written entirely by `engine/scheduler.py:179-188` (`_save_run_log`) and read by `dashboard_api.py` (`/api/videos`, `/api/regenerate-title`).
- `output/scripts/used_hooks.json` — rolling list (capped at 200) of previously-used opening sentences, read/written by `engine/script_generator.py:78-92`.
- `output/logs/engine_<date>.log` — plain-text daily log files (colorlog + file handler, `engine/utils/logger.py`).
- `output/pending_emails/*.txt` — fallback stubs when the Snapchat email fails to send.

No `CREATE TABLE` exists anywhere (no schema). No migrations exist (no `migrations/` directory, no Alembic/Django-migration tooling, no `.sql` files in this project — the only `.sql` files in the whole home-directory git history belong to the unrelated "Project Farm" repo, see §13).

State kept outside any of the above: OAuth credentials (`config/credentials/*.json`, pickled), `.env` secrets, and the raw video/audio/subtitle intermediates under `output/{audio,subtitles,videos,thumbnails}/` (transient, cleaned up after each successful compose per `video_composer.py:97-101`, `_cleanup`).

---

## 8. OPS

**APScheduler jobs:**

| id | Trigger | Interval | Registered in | Failure behaviour |
|---|---|---|---|---|
| (none set) | `interval` | `hours=<config.scheduling.interval_hours>` (4) | `engine/scheduler.py:200`, inside `start_scheduler()` (used by `main.py --schedule`) | Exceptions inside `job()` are not caught by the scheduler wrapper itself; `ViralEngine.run_pipeline()` has its own internal try/except (`scheduler.py:54-177`) that always logs and writes a failed run record, so a single failed run does not kill the scheduler loop or crash the process. |
| `"viral_pipeline_job"` | `interval` | `hours=<config.scheduling.interval_hours>` | `dashboard_api.py:196-202`, only if run as `__main__` | Same internal error handling as above (same `ViralEngine.run_pipeline()`). Note: this is a **second, independent scheduler** — see §3 concurrency warning. |

**Flask routes** (`dashboard_api.py`, all on port 5050, `debug=False`, no auth on any route):

| Route | Method | Reads/Writes | Auth |
|---|---|---|---|
| `/` | GET | serves `MAK_Socials_Dashboard.html` (static file) | none |
| `/api/status` | GET | reads in-memory scheduler state | none |
| `/api/videos` | GET | reads `output/run_log.json`, scans `output/published/` | none |
| `/api/regenerate-title` | POST | reads+writes `output/run_log.json`, calls Ollama | none |
| `/api/logs` | GET | reads latest file in `output/logs/` | none |
| `/api/run-now` | POST | spawns a background thread that runs the **full pipeline** (script gen → TTS → render → publish to YouTube/Snapchat) | **none — any unauthenticated caller on the local network can trigger a real YouTube upload** |
| `/api/engine/toggle` | POST | no-op stub (`dashboard_api.py:189-192`, does not actually toggle anything) | none |

**Logging config**: `engine/utils/logger.py`. `colorlog` console handler at `INFO`, plain `FileHandler` at `DEBUG` writing to `output/logs/engine_<YYYY-MM-DD>.log` (one file per calendar day, no rotation/size cap, no retention/cleanup policy — the March 29 log alone is 932 KB).

**Flask bind**: `app.run(port=5050, debug=False)` — `dashboard_api.py:206`. No explicit `host=` argument, so it binds to Flask's default `127.0.0.1` (localhost only, not exposed to the network by default).

---

## 9. SECURITY SCAN

**Hardcoded credentials found (file:line, variable name only — no values reproduced):**

- `.env:11` — `EMAIL_APP_PASSWORD` — populated with what appears to be a real Gmail App Password (16-character space-separated format consistent with Google's App Password generator).
- `.env:10` — `EMAIL_ADDRESS` — populated with a real-looking Gmail address.
- `.env:12` — `SNAPCHAT_EMAIL` — populated with a personal email address (routing target, not a secret, but still PII).
- `config/credentials/youtube_client_secret.json` — contains a Google OAuth `client_secret` field (standard OAuth "installed app" client secret — not silently dangerous on its own without the paired refresh token, but should not be world-readable).
- `config/credentials/youtube_token.json` — a **pickled** Python object (`pickle.dump`/`pickle.load`, `engine/uploader/youtube_uploader.py:63`/`:30`) containing a live OAuth refresh token, saved under a `.json` extension despite not being JSON. Loading this file with `pickle.load` on an attacker-modified copy would be arbitrary-code-execution risk in principle (general pickle-safety concern, not exploited here since it's self-generated).
- `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` env vars are declared in `.env` (lines 2-3) but **left blank** — the actual YouTube OAuth secret lives only in the JSON file above, so these two lines are unused placeholders.
- `IG_USER_ID` / `IG_ACCESS_TOKEN` (`.env` lines 6-7) — declared, **left blank**. Instagram publishing is effectively disabled by missing credentials (consistent with it also being commented out in code, §4 step 12).

**`.env` existence / `.gitignore` coverage**: `.env` **exists** and contains real secrets (above). **There is no `.gitignore` file anywhere in `C:\Users\ahad\MAK Socials`** — the folder has zero git configuration of its own. This is moot for accidental commits only because the folder is not tracked by any repository at all (see §13) — but that also means there is **no technical safeguard** preventing a future `git init`/`git add .` in this exact folder from committing `.env`, the OAuth client secret, and the pickled token straight into history.

**Git history secret-pattern scan** (executed exactly as specified: `git log --all -p | grep -Ein "api[_-]?key|secret|token|password"`, run from within `C:\Users\ahad\MAK Socials`, which resolves to the home-directory-rooted repo — see §13 for why):

- **Match count: 123**
- **File paths involved** (paths only, all from the unrelated "Project Farm" repo — none of them touch MAK Socials, which has no git history of its own):
  - `Project Farm/.env.example`
  - `Project Farm/.gitignore`
  - `Project Farm/BUILD_PROMPTS.md`
  - `Project Farm/CLAUDE.md`
  - `Project Farm/PRD.md`
  - `Project Farm/app/api/cron/nightly/route.ts`
  - `Project Farm/app/globals.css`
  - `Project Farm/components/Map.tsx`
  - `Project Farm/docs/superpowers/plans/2026-07-11-map-ui-filters.md`
  - `Project Farm/docs/superpowers/plans/2026-07-12-scrape-enrich-pipeline.md`
  - `Project Farm/docs/superpowers/specs/2026-07-11-map-ui-filters-design.md`
  - `Project Farm/docs/superpowers/specs/2026-07-12-scrape-enrich-pipeline-design.md`
  - `Project Farm/lib/db.ts`
  - `Project Farm/lib/enrich/geocode.ts`
  - `Project Farm/lib/enrich/parse.ts`
  - `Project Farm/lib/scrapers/apify.ts`
  - `Project Farm/lib/scrapers/firecrawl.ts`
  - `Project Farm/lib/scrapers/googleFarms.ts`
  - `Project Farm/lib/scrapers/quikr.ts`
  - `Project Farm/package-lock.json`
  - `Project Farm/scripts/trigger-cron.mjs`
- Manual spot-check confirms these are all `process.env.API_KEY`-style references, `.env.example` placeholder lines, and prose mentions of "API key"/"token" in planning docs — not literal leaked secret values. No further action taken (per instructions, values were never printed).
- **MAK Socials itself has never been committed to any git repository, so it contributes zero matches to this scan** — its real secrets (`.env`, the OAuth token) exist only on disk, not in any git history, tracked or otherwise.

No other hardcoded-credential patterns (raw API keys embedded directly in `.py` source) were found in first-party code — all uploader modules correctly source credentials from `.env`/credential files rather than inlining them.

---

## 10. PERFORMANCE

No pipeline stage was executed for this audit (per instructions). Static inspection of `output/run_log.json` and `output/logs/*.log` (real historical run data from 2026-03-29 through 2026-07-09) gives the following **observed, not measured-today**, figures:

- **Total logged runs**: 88. **Successful**: 66 (75%). **Reached YouTube upload**: 64.
- **Observed failure modes in the historical log** (frequency): a CTranslate2/torch tensor-reshape error ("cannot reshape tensor of 0 elements...", 3 occurrences — likely a Whisper edge case on unusual audio), "Failed to generate valid length audio after 3 attempts" (2), various FFmpeg render failures with Windows-specific exit codes / file-locking errors (multiple), one `Ollama model not found` error, and one `YouTube token refresh failed (invalid_grant)` — this last one is the **current** state as of the most recent log entry (2026-07-09), meaning YouTube uploads would fail today until the OAuth flow is re-run interactively.
- **Cadence**: runs cluster every ~4 hours during active periods (matches `config.yaml`'s `interval_hours: 4`), consistent with the scheduler firing as designed while it was running.
- **Pipeline has been dormant since 2026-07-09** (single, failed, apparently-manual run) — no activity in the ~47 days before this audit (today: 2026-08-25).
- Per-clip render time, Whisper model load time, and peak memory are **not recorded anywhere in the logs** (the logger does not timestamp stage boundaries finely enough to derive per-stage durations, and no profiling/metrics code exists in the repo). **These cannot be determined without actually executing the pipeline, which this audit deliberately does not do.** Stated plainly: performance timing data does not exist in this repo in any measurable static form beyond "a full run typically completed within one ~4-hour scheduling window historically."

---

## 11. VERDICT TABLE

| Module/dir | Verdict | Reason |
|---|---|---|
| `engine/scheduler.py` | **KEEP** | Correct orchestration logic; works as designed; only issue is the dual-scheduler race with `dashboard_api.py` (§3). |
| `engine/script_generator.py` | **KEEP** | Functions correctly; hardcoded premise bank is a legitimate design choice for a small niche engine. |
| `engine/tts_engine.py` | **KEEP+EXTEND** | Works, but voice list and min-duration are hardcoded and drift from `config.yaml` — worth reconciling. |
| `engine/subtitle_generator.py` | **KEEP** | Whisper word-level captioning is correctly implemented — the most important piece of the pipeline and it's solid. Ignoring `config.yaml`'s caption_style block is a real gap worth fixing (REFACTOR-lite). |
| `engine/video_composer.py` | **KEEP** | FFmpeg render logic is correct and has validation/cleanup; resolution/fps not config-driven (minor REFACTOR item). |
| `engine/utils/background_manager.py` | **REFACTOR** | Works, but the whole "random background" concept is pointless with only one file in `assets/backgrounds/`; also ignores `config.yaml`'s `resolution` key. |
| `engine/utils/music_mixer.py` | **KEEP** | Simple, correct FFmpeg mix logic. |
| `engine/thumbnail_generator.py` | **KEEP** | Works; has a bare `except:` to fix. |
| `engine/lib/title_optimizer.py` | **REFACTOR** | Redundant with the title-generation call already inside `script_generator.py:180-203` — two separate Ollama calls produce two titles, and only the second (this module's) is kept. Wasteful, confusing to trace. |
| `engine/uploader/youtube_uploader.py` | **KEEP** | Solid: retry/backoff, quota-aware, pickled-token handling is correct if slightly fragile (needs re-auth after `invalid_grant`, currently broken — see §10). |
| `engine/uploader/instagram_uploader.py` | **QUARANTINE** | Fully implemented but structurally unreachable — `scheduler.py:134` never calls it, and it requires a public video URL this repo has no way to produce. Either wire it up (needs S3/B2 hosting) or remove. |
| `engine/uploader/snapchat_emailer.py` | **KEEP** | Does exactly what it claims (email a human) — not a fake integration, just a manual-handoff one; fine as-is if that workflow is intentional. |
| `dashboard_api.py` | **REFACTOR** | Functional but has zero auth on a route that triggers real external uploads (`/api/run-now`); `flask`/`flask_cors` missing from `requirements.txt`; a no-op stub route (`/api/engine/toggle`). |
| `MAK_Socials_Dashboard.html` | **KEEP** | The actual working dashboard UI; hits `dashboard_api.py` directly. |
| `dashboard/backend/` | **DELETE** | No source code exists — only `node_modules` + a lockfile. Pure dead weight. |
| `dashboard/frontend/` | **DELETE** | Unmodified `create-next-app` scaffold, never developed past the template; has its own orphaned nested git repo. Superseded by `MAK_Socials_Dashboard.html`. |
| `n8n/` | **DELETE** | Empty directory, zero content, zero references elsewhere in the codebase. |
| `database/videos.json` | **DELETE** | Unused stub/test fixture; nothing reads or writes it. |
| `config/config.yaml` | **REFACTOR** | Several keys are dead (never read): `video.resolution`, `video.fps`, `video.duration_min`, `tts.voice`, `tts.backup_voice`. Should either be wired up or removed to stop misleading future maintainers. |
| `bulk_upload_backlog.py` | **KEEP** | Standalone, useful, correctly scoped utility for catching up missed uploads. |
| `setup.py` | **KEEP** | Legitimate first-run setup helper; two bare `except:` blocks worth tightening. |
| `assets/backgrounds/` | **KEEP+EXTEND** | The pipeline depends on this, but a single 2.29 GB clip defeats the "random" design intent and offers zero visual variety across runs. |
| `assets/music/` | **KEEP+EXTEND** | Works, but no licensing record exists for any of the 4 tracks (§6f) — needs a rights audit before continued public/monetized use. |
| `.env` / `config/credentials/` | **REFACTOR** | Functionally necessary, but plaintext secrets with no `.gitignore` protection and a pickled OAuth token are worth hardening (§9). |

---

## 12. TOP 10 RISKS (ranked by severity)

1. **No rights/licensing record for the background video or any of the 4 background music tracks**, while the pipeline uploads to a `public`, apparently monetization-intended YouTube channel every run. This is a real copyright-strike / demonetization / channel-termination risk and the single biggest business risk in the repo (§6f).
2. **Zero project-level version control.** `C:\Users\ahad\MAK Socials` has never been committed to git. There is no history, no rollback point, no backup beyond whatever is on this one disk. A local file-system failure loses the entire project irrecoverably (§13).
3. **Unauthenticated `/api/run-now` endpoint** (`dashboard_api.py:178-187`) triggers a real, unauthenticated pipeline run including a live YouTube upload, from any client that can reach port 5050 — no auth, no rate limit, no CSRF protection.
4. **YouTube OAuth refresh token is currently invalid** (`invalid_grant` on the last recorded run, 2026-07-09) — the pipeline cannot upload to YouTube today without an interactive re-authentication (`flow.run_local_server`), which is incompatible with unattended/scheduled operation.
5. **Dual, uncoordinated APScheduler instances** (`engine/scheduler.py:200` and `dashboard_api.py:197-202`) can both fire the same 4-hour job independently if `main.py --schedule` and `dashboard_api.py` are ever run at the same time, causing duplicate script generation, duplicate YouTube uploads, and wasted Ollama/FFmpeg work.
6. **Real secrets stored in plaintext with no `.gitignore` anywhere in the project** — `.env` (Gmail app password) and a pickled OAuth token sit unprotected; nothing currently stops a future `git init` in this exact folder from committing them.
7. **Pipeline has been dormant for ~47 days** (last activity 2026-07-09) with no monitoring/alerting to detect the stall — the dashboard's `/api/status` reports scheduler state but nothing pages anyone when the scheduler isn't running at all.
8. **`config.yaml` contains multiple dead/ignored keys** (`video.resolution`, `video.fps`, `video.duration_min`, `tts.voice`, `tts.backup_voice`) that silently do nothing if edited — a maintainer changing `fps: 60` in good faith would see zero effect and might not realize why, a correctness/trust hazard.
9. **`dashboard/backend/` and `dashboard/frontend/` are dead scaffolding** (no source in backend at all; frontend is unmodified boilerplate with its own orphaned nested git repo) — actively misleading to anyone auditing "what runs the dashboard," when the real answer is the single static `MAK_Socials_Dashboard.html` file served by Flask.
10. **Five bare `except:` blocks** (`setup.py:24,39`, `engine/script_generator.py:83`, `engine/scheduler.py:184`, `engine/thumbnail_generator.py:51`) silently swallow all errors including `KeyboardInterrupt`/`SystemExit` in principle, and in `scheduler.py:184` specifically can silently discard the entire run-history log on a corruption event with no backup.

---

## 13. REPO IDENTITY DISCREPANCY

**Finding, stated plainly: the git repository visible from `C:\Users\ahad\MAK Socials` has nothing to do with this codebase. It is a different project's history, and `MAK Socials` has never been committed to any git repository at all.**

Evidence, in order of discovery:

1. `git log --oneline -20` and `git log --all --oneline` (37 commits total, single branch `main`) show a coherent, self-consistent history of a **Next.js real-estate listings scraper/map app** — OLX/Quikr scraping, Firecrawl/OpenRouter enrichment, map-pin rendering, filter panels, a 50 km geo-ring helper, etc. Nothing in any of the 37 commit messages or subjects references video, TTS, Whisper, YouTube, FFmpeg, or any term related to the working directory's actual file tree (`main.py`, `engine/`, `dashboard_api.py`, etc.).
2. `git rev-parse --show-toplevel` returns **`C:/Users/ahad`** — i.e., this git repository is rooted at the **user's home directory**, not at `MAK Socials`, not at any project folder. `git config --local --list` confirms `remote.origin.url = https://github.com/Khanmohammedahad-netizen/Mak-socials.git` — so a repo whose **GitHub remote is literally named "Mak-socials"** is, in fact, tracking an entirely different, unrelated project.
3. The home directory's `.gitignore` (`C:\Users\ahad\.gitignore`) explicitly explains this setup:
   ```
   # This repo is rooted at the home directory. Scope git to Project Farm only —
   # without this, every git status/add/commit walks the entire home directory
   # (node_modules, AppData, Downloads, Android SDK, etc.), which is what was
   # causing multi-minute hangs and system lag.
   /*
   !/Project Farm/
   ```
   This ignores literally everything under the home directory except a sibling folder called **`Project Farm`** (`C:\Users\ahad\Project Farm`, confirmed to exist). `git ls-files` from the repo root returns exactly 68 files, **all** under `Project Farm/...` (confirmed: `Project Farm/app/`, `Project Farm/lib/`, `Project Farm/db/migrations/0001_init.sql`, etc. — the real-estate scraper's actual source).
   `git check-ignore -v "MAK Socials"` confirms the `MAK Socials` folder itself is caught by the `/*` ignore rule and was never eligible to be tracked.
4. `git ls-files` run from inside `C:\Users\ahad\MAK Socials` returns **zero files** — nothing in this directory is tracked, staged, or has ever been committed, despite `git status` reporting "working tree clean" (which is technically true — it's clean because none of these files are tracked, not because they match a commit).
5. Where the *actual* MAK Socials project came from: one historical log file, `output/logs/engine_2026-07-09.log:19-22`, contains a Python traceback with absolute file paths that reveal the project's original location: `C:\Users\ahad\.gemini\antigravity\scratch\MAK Socials\engine\scheduler.py`. This indicates the project was originally built by a different AI coding tool ("Gemini"/"Antigravity") inside a **scratch working directory**, and was later copied or moved to sit as a sibling of `Project Farm` directly under the home directory — landing inside the *scope* of the home-rooted git repo (since its toplevel is `C:\Users\ahad`) but never actually `git add`-ed to it, and explicitly excluded by that repo's own `.gitignore`.

**Conclusion**: This is not two projects merged in one repo, and it is not a case of misleading commit messages. It is a **git repository misconfiguration** — a repo rooted at the home directory (apparently to make life easier for one specific project, "Project Farm") that happens to have a GitHub remote confusingly named "Mak-socials," sitting adjacent to a completely different, **actually-untracked** project that also happens to be named "MAK Socials." The two share a folder-name coincidence and nothing else. Every finding in this audit about "the codebase" refers exclusively to the *files on disk* in `C:\Users\ahad\MAK Socials`, none of which have any git history, any commit authorship, or any tracked provenance. Any question that depends on "what changed and when" for this specific project **cannot be answered from git** — only from file mtimes and the run logs under `output/`, which is what Sections 7, 10, and 12 rely on instead.

**Practical implication for the user**: if `Mak-socials` on GitHub is meant to actually contain this video pipeline, that has never happened — the remote currently holds the real-estate scraper project only. Fixing this requires a deliberate decision (new repo for MAK Socials vs. renaming remotes vs. reorganizing the home-directory repo), not a git command run casually from inside this folder — running `git add` from here today would still hit the `/*` ignore rule and do nothing.
