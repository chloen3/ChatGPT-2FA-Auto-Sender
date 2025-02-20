import imaplib
import email
import re
import requests
import time
import os
from dotenv import load_dotenv
from email.header import decode_header

# Load environment variables from .env file
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = "imap.gmail.com"
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")
GROUPME_API_URL = "https://api.groupme.com/v3/bots/post"


def get_chatgpt_code():
    try:
        print("🔍 Connecting to email server...")
        mail = imaplib.IMAP4_SSL(EMAIL_HOST)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select("inbox")

        print("📩 Searching for ChatGPT verification email...")
        result, data = mail.search(None, 'UNSEEN SUBJECT "Your ChatGPT code is"')
        email_ids = data[0].split()

        print(f"📬 Found {len(email_ids)} emails matching criteria.")

        if not email_ids:
            print("❌ No new verification emails found.")
            mail.logout()
            return None

        for latest_email_id in reversed(email_ids):  # Process the latest emails first
            result, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    raw_subject = msg["Subject"]
                    decoded_subject, encoding = decode_header(raw_subject)[0]
                    if isinstance(decoded_subject, bytes):
                        subject = decoded_subject.decode(encoding or "utf-8")
                    else:
                        subject = decoded_subject

                    print(f"📝 Processing email with decoded subject: {subject}")

                    # Extract the verification code from the subject line
                    match = re.search(r"Your ChatGPT code is (\d{6})", subject)
                    if match:
                        code = match.group(1)
                        print(f"✅ Found verification code: {code}")

                        # Mark the email as read
                        mail.store(latest_email_id, '+FLAGS', '\\Seen')

                        mail.logout()
                        return code

        mail.logout()
        return None

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP error: {e}")
    except Exception as e:
        print(f"❌ Error checking email: {e}")

    return None


def send_to_groupme(code):
    try:
        message = f"ChatGPT Verification Code: {code}"
        payload = {
            "bot_id": GROUPME_BOT_ID,
            "text": message
        }
        response = requests.post(GROUPME_API_URL, json=payload)

        if response.status_code == 202:
            print("✅ Sent to GroupMe successfully.")
        else:
            print(f"❌ Failed to send message. Status Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending message to GroupMe: {e}")

# Main loop to check email every 30 seconds
while True:
    code = get_chatgpt_code()
    if code:
        print(f"🚀 Found ChatGPT Code: {code}")
        send_to_groupme(code)
    time.sleep(30)  # Check every 30 seconds
