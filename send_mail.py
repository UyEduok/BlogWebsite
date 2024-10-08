import logging
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SendMail:
    def __init__(self):
        self.EMAIL = os.getenv("EMAIL")
        self.DESTINATION_EMAIL = os.getenv("DESTINATION_EMAIL")
        self.SGRID_KEY = os.environ.get('SENDGRID_API_KEY')

    def send_email(self, body):

        message = Mail(
            from_email=self.EMAIL,
            to_emails=self.DESTINATION_EMAIL,
            subject='Contact rom Client',
            html_content=body)
        try:
            sg = SendGridAPIClient(self.SGRID_KEY)
            response = sg.send(message)
            logging.info(f"Email sent! Status code: {response.status_code}")
            logging.debug(f"Response body: {response.body}")
            logging.debug(f"Response headers: {response.headers}")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

    def respond_to_client(self, client_email):
        body = f"""
        <p>Thank you for contacting <b>Uy's blog</b>. A collection of Lovely Posts.</p><hr>
        <p>We will respond to your enquiries shortly</p><br>
        <strong>Thanks</strong>
        <strong>Uyuho Eduok<br>
        <strong>Full Stack Developer</strong>
        """
        message = Mail(
            from_email=self.EMAIL,
            to_emails=client_email,
            subject='Enquiries from Users',
            html_content=body)
        try:
            sg = SendGridAPIClient(self.SGRID_KEY)
            response = sg.send(message)
            logging.info(f"Email sent! Status code: {response.status_code}")
            logging.debug(f"Response body: {response.body}")
            logging.debug(f"Response headers: {response.headers}")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
