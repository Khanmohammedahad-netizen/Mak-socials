import os
import yaml
from ollama import Client
from engine.utils.logger import logger

class TitleOptimizer:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.ollama_client = Client(host='http://localhost:11434')
        self.model = self.config.get('ollama', {}).get('model', 'llama3.2')

    def generate_optimized_title(self, story_text: str) -> str:
        """
        Generates a viral YouTube Shorts title using Ollama.
        """
        system_prompt = """
        You are a viral YouTube Shorts title writer specializing in Reddit mystery, 
        betrayal, and drama content. Given a story summary, generate ONE title that:
        - Is under 80 characters
        - Opens with an emotional hook word (EXPOSED, She, He, I, My, They, Nobody)
        - Creates curiosity gap — never reveals the ending
        - Uses plain language, no clickbait emojis in title itself
        - Is optimized for YouTube search and monetization-safe (no profanity)
        - Ends with a cliffhanger phrase like "...and it changed everything" 
          or "...until this happened" or "...what happened next destroyed us"
        Return ONLY the title text. No explanation. No quotes.
        """
        
        try:
            logger.info("Optimizing video title with AI...")
            response = self.ollama_client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Story: {story_text}"}
                ],
                options={'temperature': 0.7}
            )
            
            title = response['message']['content'].strip()
            # Clean up quotes
            title = title.replace('"', '').replace("'", "").strip()
            
            if len(title) > 80:
                title = title[:77] + "..."
                
            logger.info(f"Generated AI Title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating AI title: {e}. Falling back to 80-char summary.")
            fallback = story_text[:80].strip()
            if len(story_text) > 80:
                fallback += "..."
            return fallback

def generate_optimized_title(story_text: str, config_path: str = "config/config.yaml") -> str:
    optimizer = TitleOptimizer(config_path)
    return optimizer.generate_optimized_title(story_text)
