import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail
import secrets
from app.config import settings


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP of specified length."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def send_otp_email(receiver_email: str, otp_code: str) -> bool:
    """
    Send OTP email using Brevo (Sendinblue) API.
    
    Args:
        receiver_email: Email address to send OTP to
        otp_code: The OTP code to send
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Raises:
        ValueError: If Brevo API key or sender email not configured
    """
    if not settings.brevo_api_key:
        raise ValueError("Brevo API key not configured. Set BREVO_API_KEY in environment.")
    
    if not settings.brevo_sender_email:
        raise ValueError("Brevo sender email not configured. Set BREVO_SENDER_EMAIL in environment.")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
            .otp-code {{ font-size: 32px; font-weight: bold; color: #4CAF50; text-align: center; padding: 20px; background-color: #f9f9f9; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Email Verification</h2>
            <p>Your verification code is:</p>
            <div class="otp-code">{otp_code}</div>
            <p>This code will expire in {settings.otp_expire_minutes} minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <div class="footer">
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.brevo_api_key
        api_instance = TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        email = SendSmtpEmail(
            sender={"email": settings.brevo_sender_email, "name": settings.brevo_sender_name},
            to=[{"email": receiver_email}],
            subject="Your Verification Code",
            html_content=html_content
        )
        
        response = api_instance.send_transac_email(email)
        return True
    except ApiException as e:
        print(f"Error sending email via Brevo: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False
