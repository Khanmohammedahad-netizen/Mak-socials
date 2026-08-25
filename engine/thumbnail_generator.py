import os
import subprocess
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from engine.utils.logger import logger

class ThumbnailGenerator:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.output_dir = os.path.join("output", "thumbnails")
        
        # Absolute Font Path Resolution
        assets_font = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Montserrat-Bold.ttf'))
        if os.path.exists(assets_font):
            self.font_path = assets_font
        else:
            self.font_path = 'C:/Windows/Fonts/arialbd.ttf' # Windows Bold Fallback
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_thumbnail(self, video_path: str, title: str, timestamp: str):
        """Generates a YouTube thumbnail from a video frame."""
        logger.info(f"Generating thumbnail for: {video_path}")
        
        # 1. Extract frame at t=2s
        frame_path = os.path.join(self.output_dir, f"temp_frame_{timestamp}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", "2", "-i", video_path,
            "-vframes", "1", "-q:v", "2", frame_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        try:
            # 2. Load and scale to 1280x720
            img = Image.open(frame_path).convert("RGBA")
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # 3. Add dark overlay for readability
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 140))
            img = Image.alpha_composite(img, overlay)
            
            draw = ImageDraw.Draw(img)
            
            # 4. Add title text
            try:
                font = ImageFont.truetype(self.font_path, 72)
                watermark_font = ImageFont.truetype(self.font_path, 28)
            except:
                logger.warning("Font not found, using default.")
                font = ImageFont.load_default()
                watermark_font = ImageFont.load_default()
            
            # Wrap text at ~22 chars
            wrapped_text = self._wrap_text(title.upper(), 22)
            
            # Draw multi-line centered text with stroke
            w, h = img.size
            # Use textbbox to get dimensions
            total_h = sum([draw.textbbox((0, 0), line, font=font)[3] for line in wrapped_text.split('\n')])
            current_y = (h - total_h) / 2
            
            for line in wrapped_text.split('\n'):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                line_h = bbox[3] - bbox[1]
                
                # Stroke
                stroke_color = (0, 0, 0, 255)
                stroke_w = 4
                for ox in range(-stroke_w, stroke_w + 1):
                    for oy in range(-stroke_w, stroke_w + 1):
                        draw.text(((w - line_w) / 2 + ox, current_y + oy), line, font=font, fill=stroke_color)
                        
                draw.text(((w - line_w) / 2, current_y), line, font=font, fill=(255, 255, 255, 255))
                current_y += line_h + 10
            
            # 5. Add subtle red gradient bar at bottom
            bar_height = 15
            draw.rectangle([0, h - bar_height, w, h], fill=(220, 20, 60, 255))
            
            # 6. Add watermark
            watermark_text = "FOLLOW FOR MORE"
            w_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
            ww, wh = w_bbox[2] - w_bbox[0], w_bbox[3] - w_bbox[1]
            draw.text((w - ww - 40, h - wh - 40), watermark_text, font=watermark_font, fill=(255, 215, 0, 255))
            
            # 7. Save final
            final_path = os.path.join(self.output_dir, f"{timestamp}.jpg")
            img.convert("RGB").save(final_path, "JPEG", quality=95)
            
            # Cleanup temp frame
            os.remove(frame_path)
            
            logger.info(f"Thumbnail created: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            if os.path.exists(frame_path):
                return frame_path # Return raw extraction as fallback
            raise

    def _wrap_text(self, text, width):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(" ".join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)

if __name__ == "__main__":
    # Test
    # gen = ThumbnailGenerator()
    pass
