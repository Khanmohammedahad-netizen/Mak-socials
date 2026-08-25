import os
import json
import random
import yaml
from datetime import datetime
from ollama import Client
from engine.utils.logger import logger

class ScriptGenerator:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.ollama_client = Client(host='http://localhost:11434')
        self.scripts_dir = os.path.join("output", "scripts")
        self.hooks_file = os.path.join(self.scripts_dir, "used_hooks.json")
        
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
            
        self.used_hooks = self._load_used_hooks()
        
        # Bank of 50+ premises
        self.premises = [
            "My wife has been 'working late' for three months, but her office moved to remote last year.",
            "I found a hidden camera in my daughter's teddy bear, and it's streaming to my neighbor's IP.",
            "My brother's new girlfriend looks exactly like our sister who disappeared ten years ago.",
            "I inherited a house from a grandfather I never knew, but the basement door is welded shut.",
            "Everyone in my town is suddenly forgetting who I am, one by one.",
            "My husband took out a massive life insurance policy on me without my knowledge.",
            "I found a list of names in my mom's drawer. Three are crossed out. Mine is next.",
            "My shadow started moving three seconds after I did this morning.",
            "I caught my 'blind' roommate reading my private diary at 3 AM.",
            "My DNA test revealed I'm not related to anyone in my family, but I have a twin in prison.",
            "I started receiving postcards from myself, dated one week into the future.",
            "My best friend's 'imaginary' childhood friend just showed up at my wedding.",
            "I found a secret room behind my wardrobe filled with photos of me sleeping.",
            "My parents told me my twin died at birth, but I just found her social media profile.",
            "I'm a teacher and one of my first-grade students draws detailed pictures of my private life.",
            "I bought a used phone and it still has 'Find My' active for a person reported missing.",
            "My husband has a second family in the next town over, and they think I'm the mistress.",
            "Every time I look in the mirror, my reflection is wearing different clothes than I am.",
            "I found a baby monitor in my attic that's picking up voices from the 1950s.",
            "My sister-in-law is slowly poisoning my brother, and I'm the only one who sees it.",
            "I discovered my boss is using my identity to launder millions through shell companies.",
            "My dog only barks at the corner of my room where 'nothing' is standing.",
            "I found a wedding ring in my boyfriend's pocket, but the engraving is for someone else.",
            "My neighbor hasn't left his house in 20 years, but I see a different person every night.",
            "I'm a nanny and the 'parents' never actually come home, they just send wire transfers.",
            "I found a tunnel under my garden that leads directly into the local police station.",
            "My girlfriend's 'identical twin' is actually just her with a wig and a fake accent.",
            "I started hearing my own voice coming from inside the walls of my new apartment.",
            "My grandmother's 'antique' locket contains a microchip dated 2045.",
            "Everyone at my company is a robot, and I only figured it out because of a power surge.",
            "I found my own obituary in a newspaper from fifty years ago.",
            "My cat brings me 'gifts' that are actually pieces of evidence from unsolved crimes.",
            "I discovered my wife isn't human after she forgot to blink for twenty minutes.",
            "My childhood home was demolished, but I just walked past it on my way to work.",
            "I found a diary in the trash that describes exactly what I'm going to do tomorrow.",
            "My boyfriend is perfect, except he has no heartbeat and his skin is always cold.",
            "I'm the only person who can see the 'Help Me' signs in my neighbor's windows.",
            "My parents sold me to a secret organization when I was five, and they just came to collect.",
            "I found a hidden vault in my basement filled with gold bars and a photo of my boss.",
            "My best friend died in a car crash, but he just called me to say he's hiding.",
            "I discovered my roommates have been filming a reality show about me for years.",
            "My husband's 'workout' videos are actually encoded messages for a foreign agency.",
            "I found a map of my house with 'X' marks where bodies are supposedly buried.",
            "My daughter is talking to a 'friend' in the mirror who looks exactly like me at her age.",
            "I started seeing a countdown clock in the sky that only I can perceive.",
            "My lottery win was 'arranged' by a stranger who now wants a terrifying favor.",
            "I found a thumb drive in a library book containing the names of every undercover agent.",
            "My 'dead' father has been leaving me voicemails for the last ten years.",
            "I discovered my quiet town is actually a massive social experiment for a big tech firm.",
            "My wife's 'secret' recipe is actually a slow-acting mind control substance.",
            "I found a trapdoor under my rug that leads to an exact replica of my house, but dark."
        ]

    def _load_used_hooks(self):
        if os.path.exists(self.hooks_file):
            try:
                with open(self.hooks_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_used_hook(self, hook: str):
        self.used_hooks.append(hook)
        if len(self.used_hooks) > 200:
            self.used_hooks = self.used_hooks[-200:]
        with open(self.hooks_file, "w") as f:
            json.dump(self.used_hooks, f)

    def generate(self):
        sub_variant = random.choice(self.config['niche']['sub_variants'])
        premise = random.choice(self.premises)
        
        logger.info(f"Generating script for variant: {sub_variant}")
        logger.debug(f"Premise: {premise}")

        system_prompt = """
You are the world's best viral short-form scriptwriter. 
Your scripts consistently hit 90%+ retention on YouTube Shorts 
and command $12+ CPM due to high viewer engagement signals.

MANDATORY STRUCTURE — every script must follow this arc:
1. HOOK (first 8 words): Start with the most shocking or 
   intriguing moment. No warmup. No "so basically". Drop the 
   viewer into the middle of the story.
2. CONTEXT (next 2-3 sentences): Who, what, where — fast.
3. ESCALATION (middle section): Each sentence raises the stakes. 
   Use short punchy sentences mixed with longer ones. Build dread 
   or anticipation. Never resolve tension early.
4. TWIST or REVELATION: One moment that reframes everything. 
   This is what makes people comment and share.
5. PAYOFF + CTA (final 2 sentences): Satisfying ending. 
   End with: "Follow for more stories like this."

STRICT RULES — never break these:
- Word count: 160-180 words exactly. Count before responding.
- First person "I" POV always — creates emotional intimacy
- Every sentence must earn its place — cut anything that 
  doesn't escalate tension or reveal character
- No filler: "basically", "literally", "you know", "so yeah"
- No passive voice — use active, punchy verbs
- Vary sentence length aggressively: mix 3-word punches with 
  longer builds. Example rhythm: "I froze. My hands went cold. 
  The message on his phone was addressed to my sister."
- Use specific details that feel real: ages, times, 
  relationships, locations. "My coworker" is weak. 
  "My coworker of 6 years, Sarah" is strong.
- The twist must be genuinely surprising — not predictable
- Write for AUDIO — read it aloud mentally. It must flow 
  naturally when spoken at 1.0x speed.
- End EVERY script with exactly: 
  "Follow for more stories like this."
- Output ONLY the raw script. No labels, no titles, 
  no stage directions, no word count.
        """

        openers = [
            "I found something I was never supposed to see",
            "My [person] has been lying to me for [time]",
            "Everyone said I was overreacting. Then I found the proof.",
            "I only had 5 minutes to decide. I made the wrong choice.",
            "Nobody believed me until it was too late."
        ]
        
        # Filter out used openers if needed, or just pick one
        opener_base = random.choice(openers)
        
        user_prompt = f"""
        Write a 160–180 word first-person {sub_variant} story for a YouTube Short. 
        The story is about: {premise}.
        Hook must include one of these openers (pick one, don't use it verbatim): 
        {opener_base}
        Make the ending a genuine payoff, not a cliffhanger.
        """

        try:
            response = self.ollama_client.generate(
                model=self.config['ollama']['model'],
                system=system_prompt,
                prompt=user_prompt,
                options={
                    'temperature': self.config['ollama']['temperature'],
                    'num_predict': self.config['ollama']['max_tokens']
                }
            )
            
            script_text = response['response'].strip()
            
            # Post-processing
            if "Follow for more stories like this." not in script_text:
                if not script_text.endswith("."):
                    script_text += "."
                script_text += " Follow for more stories like this."
            
            # Generate Title
            title_system = """
You write YouTube Shorts titles that get clicked. 
Rules:
- Max 55 characters
- Must create a knowledge gap — reader MUST watch to resolve it
- Use one of these proven structures:
  * "I [did something] and [shocking consequence]"
  * "My [person] [did something unthinkable]"  
  * "The [thing] that [destroyed/changed/ended] everything"
  * "Nobody told me [shocking truth]"
- Use emotionally charged words: exposed, betrayed, destroyed, 
  secret, truth, finally, caught, lied, hidden
- No clickbait that the video doesn't deliver on
- No quotation marks in the title
- Output ONLY the title. Nothing else.
            """
            title_user = f"Write one title for this script: {script_text[:100]}"
            
            title_response = self.ollama_client.generate(
                model=self.config['ollama']['model'],
                system=title_system,
                prompt=title_user
            )
            title = title_response['response'].strip().replace('"', '')

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_filename = f"{timestamp}.txt"
            script_path = os.path.join(self.scripts_dir, script_filename)
            
            with open(script_path, "w") as f:
                f.write(script_text)
            
            # Extract actual hook used to track
            first_sentence = script_text.split('.')[0]
            self._save_used_hook(first_sentence)

            return {
                "script": script_text,
                "title": title,
                "variant": sub_variant,
                "path": script_path,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise

if __name__ == "__main__":
    # Test block
    gen = ScriptGenerator()
    print(gen.generate())
