import os
import smtplib
import yaml
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from engine.utils.logger import logger

class SnapchatEmailer:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        from dotenv import load_dotenv
        load_dotenv()
        
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.app_password = os.getenv("EMAIL_APP_PASSWORD")
        self.target_email = os.getenv("SNAPCHAT_EMAIL") or self.config['snapchat']['email_to']

    def send_video(self, video_path: str, title: str, script: str):
        if not self.email_address or not self.app_password:
            logger.warning("Email credentials missing in .env. Skipping Snapchat delivery.")
            return False

        logger.info(f"Sending Snapchat delivery email for: {title}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = self.target_email
        msg['Subject'] = self.config['snapchat']['subject_template'].format(title=title) + f" [{timestamp}]"

        body_html = f"""
        <html>
            <body>
                <h2 style='color: #FFFC00;'>SNAPCHAT SPOTLIGHT DELIVERY 🎬</h2>
                <p><b>Video Title:</b> {title}</p>
                <hr>
                <p><b>Suggested Caption:</b><br>{script[:200]}...</p>
                <p><b>Posting Checklist:</b></p>
                <ul>
                    <li>Post to Snapchat Spotlight & Map</li>
                    <li>Ensure it's 60s+ for revenue sharing (loop if needed)</li>
                    <li>Use trending sounds at 1% volume</li>
                </ul>
                <p><i>Sent via Viral Content Engine</i></p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body_html, 'html'))

        # Attachment
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        if file_size < 25:
            try:
                with open(video_path, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(video_path)}")
                    msg.attach(part)
                logger.info("Video correctly attached to email.")
            except Exception as e:
                logger.error(f"Error attaching video: {e}")
        else:
            logger.warning(f"Video file too large ({file_size:.2f}MB) to attach. Sending path only.")
            msg.attach(MIMEText(f"\nVIDEO TOO LARGE TO ATTACH.\nLocal File Path: {video_path}", 'plain'))

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)
            logger.info("Snapchat delivery email sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            # Save for fallback
            pending_dir = os.path.join("output", "pending_emails")
            if not os.path.exists(pending_dir): os.makedirs(pending_dir)
            with open(os.path.join(pending_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"), "w") as f:
                f.write(f"Subject: {msg['Subject']}\nPath: {video_path}")
            return False

if __name__ == "__main__":
    # Test
    # sc = SnapchatEmailer()
    pass
