import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import config

def send_leads_report(recipient_email: str, docx_path: str, csv_path: str, num_leads: int):
    """Sends generated lead report files as attachments via SMTP."""
    print(f"[EMAIL] Preparing email to send reports to {recipient_email}...")
    
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("[WARNING] SMTP credentials not set in environment. Skipping email sending.")
        print("Tip: Update your SMTP settings in .env to enable email delivery.")
        return
        
    msg = MIMEMultipart()
    msg['From'] = config.SMTP_USER
    msg['To'] = recipient_email
    msg['Subject'] = f"Timidly Inc: Lead Generation Report - {num_leads} Leads Generated"
    
    body = (
        f"Hello,\n\n"
        f"Please find attached the target leads report. A total of {num_leads} leads were successfully processed.\n"
        f"The report includes detailed contact details, backgrounds, headquarters, and AI-tailored pitches for Timidly Inc.\n\n"
        f"Best regards,\n"
        f"Timidly Inc Lead Generator Script"
    )
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach files
    for filepath in [docx_path, csv_path]:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                msg.attach(part)
        else:
            print(f"[WARNING] Attachment not found: {filepath}")
                
    try:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, recipient_email, msg.as_string())
        server.quit()
        print(f"[OK] Successfully sent report email to {recipient_email}!")
    except Exception as e:
        print(f"[FAIL] Failed to send email via SMTP: {e}")
        raise
