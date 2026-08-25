import os
import time
import pickle
import yaml
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import traceback
from engine.utils.logger import logger

class YouTubeUploader:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
        self.credentials_file = "config/credentials/youtube_client_secret.json"
        self.token_file = "config/credentials/youtube_token.json"
        self.youtube = self._get_service()

    def _get_service(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading existing YouTube token: {e}")
                creds = None
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing YouTube access token...")
                    creds.refresh(Request())
                else:
                    raise Exception("No existing valid token found to refresh")
            except (RefreshError, Exception) as e:
                logger.warning(f"YouTube token refresh failed: {e}. Starting new authentication flow...")
                
                # If refresh fails, it's often because the token was revoked or expired.
                # Deleting the invalid token file ensures we start fresh.
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                
                if not os.path.exists(self.credentials_file):
                    logger.error(f"YouTube credentials file not found at {self.credentials_file}")
                    logger.error("Please ensure your Google Cloud 'client_secret.json' is in the config/credentials folder.")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            try:
                os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("YouTube token saved successfully.")
            except Exception as e:
                logger.error(f"Failed to save YouTube token: {e}")

        return build("youtube", "v3", credentials=creds)

    def upload_video(self, video_path: str, title: str, description: str, thumbnail_path: str = None):
        if not self.youtube:
            logger.error("YouTube service not initialized. Skipping upload.")
            return None

        if not os.path.exists(video_path):
            logger.error(f"Upload aborted: Video file not found at {video_path}")
            return None

        logger.info(f"Uploading video to YouTube: {title}")
        
        # Curated description with first 2 sentences of the story summary
        sentences = [s.strip() for s in description.split('.') if s.strip()]
        summary = ". ".join(sentences[:2])
        if summary and not summary.endswith('.'):
            summary += '.'
            
        full_description = f"{summary}\n\n🔔 Subscribe — new stories every 4 hours.\n#Shorts #Reddit #Mystery #Drama #Storytime #Betrayal #FamilyDrama"
        
        # Specified mystery niche tags
        tags = ["shorts", "reddit", "mystery", "storytime", "drama", "betrayal", "family drama", "true story", "reddit stories", "viral shorts"]
        
        body = {
            'snippet': {
                'title': title[:100],
                'description': full_description,
                'tags': tags,
                'categoryId': self.config['youtube'].get('category_id', '22')
            },
            'status': {
                'privacyStatus': self.config['youtube'].get('privacy', 'public'),
                'selfDeclaredMadeForKids': False
            }
        }

        try:
            insert_request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )

            video_id = self._execute_upload_with_retry(insert_request)
            
            if video_id and thumbnail_path:
                if os.path.exists(thumbnail_path):
                    self._set_thumbnail(video_id, thumbnail_path)
                else:
                    logger.warning(f"Thumbnail file not found at {thumbnail_path}, skipping thumbnail upload.")
                
            if video_id:
                url = f"https://youtube.com/shorts/{video_id}"
                logger.info(f"YouTube Upload Successful! URL: {url}")
                return video_id
        except Exception as e:
            logger.error(f"An unexpected error occurred during upload preparation: {e}")
            logger.error(traceback.format_exc())
            
        return None

    def _execute_upload_with_retry(self, request, max_retries=5):
        response = None
        retry = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        return response['id']
                    else:
                        logger.error(f"Upload completed but no ID returned: {response}")
                        return None
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error_msg = f"Retriable HTTP error {e.resp.status} occurred."
                elif e.resp.status == 403:
                    if b"quotaExceeded" in e.content:
                        logger.error("YouTube API Quota Exceeded. Finalizing attempts.")
                        return None
                    elif b"limitExceeded" in e.content:
                        logger.error("YouTube daily upload limit reached. Cannot proceed.")
                        return None
                    else:
                        logger.error(f"Permission or Forbidden error (403): {e.content}")
                        return None
                else:
                    logger.error(f"Non-retriable HTTP error {e.resp.status}: {e.content}")
                    return None
            except Exception as e:
                error_msg = f"A retriable error occurred: {e}"

            # If we reached here, it's a retriable error
            logger.warning(f"{error_msg} Retry {retry + 1}/{max_retries}...")
            retry += 1
            if retry >= max_retries:
                logger.error("Max retries exceeded for this upload.")
                return None
            
            wait_time = (2 ** retry) + (1 * retry) # Exponential backoff + jitter
            time.sleep(wait_time)
        return None

    def _set_thumbnail(self, video_id, thumbnail_path):
        try:
            logger.info("Setting thumbnail...")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")

if __name__ == "__main__":
    # Test
    # up = YouTubeUploader()
    pass
