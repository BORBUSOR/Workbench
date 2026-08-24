import os
import smtplib
from email.message import EmailMessage

def send_email_with_attachments(recipient_email, attachment_paths, subject, body_html):
    """Sends dispatched files via secure SMTP SSL with multi-attachment support."""
    auth_email = os.getenv("SENDER_EMAIL")
    auth_password = os.getenv("SENDER_PASSWORD")
    display_from = os.getenv("OUTBOUND_FROM", "Zodiac Custom Shop <noreply@zodiaccustomshop.com>")
    
    if not auth_email or not auth_password:
        raise ValueError("SMTP credentials (.env) are missing or empty.")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = display_from
    msg['To'] = recipient_email
    msg.set_content("Your ZCS schedule conversion files or support request are attached.")
    msg.add_alternative(body_html, subtype='html')
    
    # Loop through all provided file paths and attach them safely
    for path in attachment_paths:
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                filename = os.path.basename(path)
                maintype = 'application'
                subtype = 'octet-stream'
                
                if path.endswith('.pdf'):
                    subtype = 'pdf'
                elif path.endswith('.ics'):
                    maintype = 'text'
                    subtype = 'calendar'
                elif path.endswith(('.png', '.jpg', '.jpeg')):
                    maintype = 'image'
                    subtype = 'png'
                    
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=filename)
                
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(auth_email, auth_password)
                server.send_message(msg)
        except Exception as smtp_err:
            raise ConnectionError(f"SMTP Transmission Failed:\n{str(smtp_err)}")