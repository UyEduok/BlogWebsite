import smtplib
import os
import logging
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SendMail:
    def __init__(self):
        self.EMAIL = os.getenv("EMAIL")
        self.PASSWORD = os.getenv("PASSWORD")
        self.DESTINATION_EMAIL = os.getenv("DESTINATION_EMAIL")

    def send_email(self,body):
        try:
            # Create an EmailMessage object
            msg = EmailMessage()
            msg['Subject'] = "Client Enquiry"
            msg['From'] = self.EMAIL
            msg['To'] = self.DESTINATION_EMAIL
            msg.set_content(body)

            # Send the email
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=self.EMAIL, password=self.PASSWORD)
                connection.send_message(msg)

            logging.info("Email sent successfully!")
        except smtplib.SMTPAuthenticationError:
            logging.error("Authentication failed. Check your email and app password.")
        except smtplib.SMTPConnectError:
            logging.error("Failed to connect to the SMTP server. Check your network and SMTP settings.")
        except smtplib.SMTPException as e:
            logging.error(f"An SMTP error occurred: {e}")
        except TimeoutError:
            logging.error("Connection timed out. Check your network connection.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

