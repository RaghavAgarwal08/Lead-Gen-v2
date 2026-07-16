import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import config

def send_leads_report(recipient_email: str, docx_path: str, csv_path: str, num_leads: int):
    """Sends generated lead report files as attachments via SMTP or Resend API."""
    print(f"[EMAIL] Preparing email to send reports to {recipient_email}...")
    
    # Check if Resend API Key is configured for Render free tier support
    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        print("[EMAIL] RESEND_API_KEY detected. Using Resend HTTP API for delivery...")
        import base64
        import requests
        
        body = (
            f"Hello,\n\n"
            f"Please find attached the target leads report. A total of {num_leads} leads were successfully processed.\n"
            f"The report includes detailed contact details, backgrounds, headquarters, and AI-tailored pitches for Timidly Inc.\n\n"
            f"Best regards,\n"
            f"Timidly Inc Lead Generator Script"
        )
        
        attachments_list = []
        for filepath in [docx_path, csv_path]:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                with open(filepath, "rb") as attachment:
                    content_b64 = base64.b64encode(attachment.read()).decode("utf-8")
                    attachments_list.append({
                        "content": content_b64,
                        "filename": filename
                    })
            else:
                print(f"[WARNING] Attachment not found: {filepath}")
                
        payload = {
            "from": "Timidly Lead Gen <onboarding@resend.dev>",
            "to": recipient_email,
            "subject": f"Timidly Inc: Lead Generation Report - {num_leads} Leads Generated",
            "text": body,
            "attachments": attachments_list
        }
        
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            r = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=20)
            if r.status_code in [200, 201]:
                print(f"[OK] Successfully sent report email via Resend HTTP API to {recipient_email}!")
                return
            else:
                print(f"[FAIL] Resend API error (HTTP {r.status_code}): {r.text}. Attempting fallback to SMTP...")
        except Exception as e:
            print(f"[WARNING] Resend API call failed: {e}. Attempting fallback to SMTP...")
            
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        print("[WARNING] SMTP credentials not set in environment. Skipping email sending.")
        print("Tip: Update your SMTP settings or configure RESEND_API_KEY in .env to enable email delivery.")
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
        if config.SMTP_PORT == 465:
            print("[EMAIL] Connecting via SMTP_SSL (port 465)...")
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        else:
            print(f"[EMAIL] Connecting via SMTP (port {config.SMTP_PORT})...")
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
            server.starttls()
            
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, recipient_email, msg.as_string())
        server.quit()
        print(f"[OK] Successfully sent report email to {recipient_email}!")
    except Exception as e:
        print(f"[EMAIL] SMTP connection/sending failed on port {config.SMTP_PORT}: {e}")
        # Fallback to port 465 if we attempted port 587 or others
        if config.SMTP_PORT != 465:
            print("[EMAIL] Attempting fallback to port 465 via SMTP_SSL...")
            try:
                server = smtplib.SMTP_SSL(config.SMTP_HOST, 465, timeout=15)
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.sendmail(config.SMTP_USER, recipient_email, msg.as_string())
                server.quit()
                print(f"[OK] Successfully sent report email to {recipient_email} via fallback port 465!")
                return
            except Exception as fallback_err:
                print(f"[FAIL] Fallback to port 465 also failed: {fallback_err}")
                raise fallback_err
        raise e

