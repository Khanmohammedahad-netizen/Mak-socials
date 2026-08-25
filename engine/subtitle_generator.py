import os
import whisper
import yaml
import unicodedata
from datetime import datetime
from engine.utils.logger import logger

class SubtitleGenerator:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.subtitles_dir = os.path.join("output", "subtitles")
        if not os.path.exists(self.subtitles_dir):
            os.makedirs(self.subtitles_dir)
            
        logger.info("Loading Whisper model ('base')...")
        self.model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully.")

    def generate_ass(self, audio_path: str, timestamp: str, words_per_chunk: int = 3) -> dict:
        """Generates an ASS subtitle file from Whisper word-level timestamps."""
        logger.info(f"Transcribing audio for ASS: {audio_path}")
        
        # 1. Run Whisper transcription with word_timestamps=True
        result = self.model.transcribe(
            audio_path, 
            word_timestamps=True,
            language='en'
        )
        
        # 2. Extract word-level timestamps from result["segments"]
        words = []
        for segment in result["segments"]:
            for word_data in segment.get("words", []):
                words.append({
                    "word": word_data["word"].strip().upper(),
                    "start": word_data["start"],
                    "end": word_data["end"]
                })
        
        logger.info(f"Extracted {len(words)} words.")
        
        # 3. Smart chunking — sentence-aware with punctuation handling
        def chunk_words(word_list: list, size: int = 3) -> list:
            result_chunks = []
            current_chunk = []
            
            for i, word_data in enumerate(word_list):
                word = word_data["word"].strip()
                
                # Skip empty words
                if not word:
                    continue
                
                display_word = word.upper()
                
                # Remove standalone punctuation tokens — attach to previous chunk
                if display_word in [".", ",", "!", "?", "...", "-", "\u2014"]:
                    if current_chunk:
                        prev = current_chunk[-1]
                        clean = prev["word"].rstrip(".,!?")
                        if display_word in [".", "!", "?"]:
                            current_chunk[-1] = {**prev,
                                "word": clean + display_word}
                        elif display_word == ",":
                            current_chunk[-1] = {**prev,
                                "word": clean + ","}
                    continue
                
                current_chunk.append({
                    "word": display_word,
                    "start": word_data["start"],
                    "end": word_data["end"]
                })
                
                # Determine if we should end the chunk here
                should_break = False
                
                # Break on natural sentence endings
                if any(display_word.endswith(p) for p in [".", "!", "?"]):
                    should_break = True
                # Break on chunk size limit
                elif len(current_chunk) >= size:
                    should_break = True
                
                # Flush chunk
                if should_break and current_chunk:
                    result_chunks.append({
                        "text": " ".join(w["word"] for w in current_chunk),
                        "start": current_chunk[0]["start"],
                        "end": current_chunk[-1]["end"]
                    })
                    current_chunk = []
            
            # Flush remaining words
            if current_chunk:
                result_chunks.append({
                    "text": " ".join(w["word"] for w in current_chunk),
                    "start": current_chunk[0]["start"],
                    "end": current_chunk[-1]["end"]
                })
            
            return result_chunks
        
        chunks = chunk_words(words, size=words_per_chunk)
            
        # 4. Clean each chunk text for ASS compatibility
        def clean_for_ass(text: str) -> str:
            # Replace smart quotes and apostrophes
            text = text.replace('\u2019', "'")
            text = text.replace('\u2018', "'")  
            text = text.replace('\u201c', '"')
            text = text.replace('\u201d', '"')
            # Remove ASS special chars that break parsing
            text = text.replace('{', '').replace('}', '')
            text = text.replace('\\', '')
            # Strip unprintable/non-ASCII chars
            text = ''.join(c for c in text if unicodedata.category(c) != 'Cc')
            return text.strip()

        # 5. Convert seconds to ASS timestamp format H:MM:SS.cc
        def to_ass_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            cs = int((seconds % 1) * 100)
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        # 6. Write the ASS file with high-retention viral style
        ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,90,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        lines = [ASS_HEADER]
        for i, chunk in enumerate(chunks):
            # Adjust timing: slight lead-in and buffer after last word
            adjusted_start = max(0, chunk["start"] - 0.05)
            adjusted_end = chunk["end"] + 0.1
            # Prevent overlap with next chunk
            if i < len(chunks) - 1:
                next_start = chunks[i + 1]["start"] - 0.05
                adjusted_end = min(adjusted_end, next_start - 0.01)
            
            start = to_ass_time(adjusted_start)
            end = to_ass_time(adjusted_end)
            text = clean_for_ass(chunk["text"])
            lines.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
            )
        
        ass_path = os.path.join(self.subtitles_dir, f"{timestamp}.ass")
        # Ensure UTF-8 with BOM for ASS compatibility on some Windows systems
        with open(ass_path, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(lines))
            
        logger.info(f"Generated ASS subtitle file: {ass_path}")
        return {
            "ass_path": ass_path,
            "word_count": len(words)
        }

if __name__ == "__main__":
    # Test block
    gen = SubtitleGenerator()
    # print(gen.generate_ass("output/audio/test_tts_processed.mp3", "test_ass"))
