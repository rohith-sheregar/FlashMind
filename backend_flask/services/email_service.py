"""Email service for sending OTP verification emails via SMTP."""
import smtplib
import random
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

try:
    from backend_flask.config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT
except ModuleNotFoundError:
    from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT


def generate_otp(length=6):
    """Generate a random numeric OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send an OTP verification email to the given address.
    
    Returns True on success, False on failure.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env")
        return False

    subject = "FlashMind - Verify Your Email"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 0; }}
            .container {{ max-width: 500px; margin: 40px auto; background: #1e293b; border-radius: 16px; padding: 40px; border: 1px solid rgba(139, 92, 246, 0.3); }}
            .logo {{ text-align: center; font-size: 28px; font-weight: 700; color: #a78bfa; margin-bottom: 8px; }}
            .subtitle {{ text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 32px; }}
            .otp-box {{ background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15)); border: 2px solid rgba(139, 92, 246, 0.4); border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-size: 36px; font-weight: 700; letter-spacing: 12px; color: #a78bfa; font-family: 'Courier New', monospace; }}
            .message {{ color: #94a3b8; font-size: 14px; line-height: 1.6; text-align: center; }}
            .warning {{ color: #f59e0b; font-size: 12px; text-align: center; margin-top: 24px; }}
            .footer {{ text-align: center; color: #475569; font-size: 12px; margin-top: 32px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🧠 FlashMind</div>
            <div class="subtitle">AI Study Companion</div>
            <p class="message">Welcome! Please use the following code to verify your email address:</p>
            <div class="otp-box">
                <div class="otp-code">{otp}</div>
            </div>
            <p class="message">This code is valid for <strong>5 minutes</strong>.</p>
            <p class="warning">⚠️ If you didn't request this, please ignore this email.</p>
            <div class="footer">© 2026 FlashMind. All rights reserved.</div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['From'] = f"FlashMind <{SMTP_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    # Plain text fallback
    plain_text = f"Your FlashMind verification code is: {otp}\n\nThis code is valid for 5 minutes.\nIf you didn't request this, please ignore this email."
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check SMTP_EMAIL and SMTP_PASSWORD.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending OTP to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending OTP to {to_email}: {e}")
        return False
