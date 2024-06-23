import smtplib
import httpx
import logging
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(recipient_email, subject, body, app_config):
    mail_server = app_config['mail_server']
    mail_port = app_config['mail_port']
    default_sender = app_config['mail_default_sender']
    mail_password = app_config['mail_password']
    mail_username = app_config['mail_username']

    msg = MIMEMultipart()
    msg['From'] = default_sender
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            text = msg.as_string()
            server.sendmail(default_sender, recipient_email, text)
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
    except Exception as e:
        logger.error(f"Failed to send email due to: {e}")
        return False

def send_teams_notification(state, app_config):
    try:
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "New KB Article Published",
            "sections": [{
                "activityTitle": f"New Article Published: {state['title']}",
                "activitySubtitle": "Please review the new article in ServiceNow.",
                "activityImage": "https://www.servicenow.com/etc.clientlibs/servicenow/clientlibs/clientlib-base/resources/images/brand/logo-full-color.svg",
                "facts": [
                    {"name": "Description", "value": f"Hello,\n\nA new article titled '{state['title']}' has been published. Please check it out in ServiceNow and provide your feedback.\n\n**Summary:** {state['summary']}\n\n[View Article]({state['article_url']})\n\nSent by: AI4KBAgent™"},
                    {"name": "KB Article URL", "value": state['article_url']}
                ],
                "markdown": True
            }]
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        response = httpx.post(app_config['teams_webhook_url'], headers=headers, json=message)
        if response.status_code == 200:
            logger.info("Notification sent to Microsoft Teams successfully")
        else:
            logger.error(f"Failed to send notification to Microsoft Teams. Status code: {response.status_code}")

    except Exception as e:
        logger.error(f"Exception in send_teams_notification: {e}")
            

        

def send_email_notification(state, app_config):
    try:
        #logger.info(f"Starting send_email_notification: {state}")
        recipient_email = app_config["email_address"]
        subject = f"New KB Article Published - {state['title']}"
        body = (f"Hello,\n\nA new article titled '{state['title']}' has been published. "
                f"Please check it out in ServiceNow and provide your feedback.\n\n"
                f"**Summary:** {state['summary']}\n\n"
                f"You can view the article here: {state['article_url']}\n\n"
                f"Sent by: AI4KBAgent™")
        
        if send_email(recipient_email, subject, body, app_config):
            logger.info("Email sent successfully")
        else:
            logger.error("Failed to send email")
    except Exception as e:
        logger.error(f"Exception in send_email_notification: {e}")

def create_service_now_kb(state, app_config):
    try:
        #logger.info(f"app_config: {app_config}")

        def encode_credentials(username, password):
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
            return encoded_credentials

        # Extract relevant data from state
        title = state['title']
        summary = state['summary']
        sections = state['sections']

        # Build the content for ServiceNow KB Article
        content = f"<h1>{title}</h1><p>{summary}</p>"
        for section in sections:
            content += f"<h2>{section['section_name']}</h2><p>{section['content']}</p>"

        url = f"{app_config['servicenow_instance']}/api/now/table/kb_knowledge"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {encode_credentials(app_config['servicenow_username'], app_config['servicenow_password'])}"
        }
        data = {
            "short_description": title,
            "text": content,
            "kb_category": state['category'],
            "workflow_state": "published"
        }
        response = httpx.post(url, headers=headers, json=data)
        if response.status_code == 201:
            kb_sys_id = response.json()["result"]["sys_id"]
            kb_url = f"{app_config['servicenow_instance']}/kb_view.do?sys_kb_id={kb_sys_id}"
            logger.info(f"KB Article created successfully: {kb_sys_id}")

            state["article_url"] = kb_url
        else:
            logger.error(f"Failed to create KB Article. Status code: {response.status_code}")
            raise Exception(f"Failed to create KB Article. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Exception in create_service_now_kb: {e}")
        raise

    return state
