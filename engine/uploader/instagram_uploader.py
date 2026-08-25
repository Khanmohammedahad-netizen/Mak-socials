import os
import time
import requests
import yaml
from engine.utils.logger import logger

class InstagramUploader:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        from dotenv import load_dotenv
        load_dotenv()
        
        self.user_id = os.getenv("IG_USER_ID")
        self.access_token = os.getenv("IG_ACCESS_TOKEN")
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.user_id}"

    def upload_reel(self, video_url: str, caption: str):
        """Uploads a Reel to Instagram via Graph API."""
        if not self.user_id or not self.access_token:
            logger.error("Instagram credentials missing in .env. Skipping Instagram upload.")
            return None

        logger.info("Starting Instagram Reel upload process...")
        
        # Step 1: Create Container
        container_url = f"{self.base_url}/media"
        params = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": self.config['instagram']['reel_share_to_feed'],
            "access_token": self.access_token
        }
        
        try:
            resp = requests.post(container_url, data=params)
            resp_data = resp.json()
            if "id" not in resp_data:
                logger.error(f"Instagram container creation failed: {resp_data}")
                return None
            
            container_id = resp_data["id"]
            logger.info(f"IG Container created: {container_id}")
            
            # Step 2: Poll for status
            if not self._wait_for_container(container_id):
                return None
                
            # Step 3: Publish
            publish_url = f"{self.base_url}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            publish_resp = requests.post(publish_url, data=publish_params)
            publish_data = publish_resp.json()
            
            if "id" in publish_data:
                logger.info(f"Instagram Reel published: {publish_data['id']}")
                return publish_data["id"]
            else:
                logger.error(f"Instagram publish failed: {publish_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error during Instagram upload: {e}")
            return None

    def _wait_for_container(self, container_id, timeout=120):
        start_time = time.time()
        logger.info("Polling Instagram container status...")
        
        status_url = f"https://graph.facebook.com/{self.api_version}/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": self.access_token
        }
        
        while time.time() - start_time < timeout:
            resp = requests.get(status_url, params=params)
            status = resp.json().get("status_code")
            if status == "FINISHED":
                logger.info("IG Container status: FINISHED")
                return True
            elif status == "ERROR":
                logger.error(f"IG Container processing error: {resp.json()}")
                return False
            
            logger.debug(f"IG Status: {status}, retrying in 5s...")
            time.sleep(5)
            
        logger.error("IG Container processing timed out.")
        return False

if __name__ == "__main__":
    # Test
    # ig = InstagramUploader()
    pass
