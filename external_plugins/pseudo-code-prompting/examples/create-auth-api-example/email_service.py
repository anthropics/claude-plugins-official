from typing import Optional
from config import settings

class EmailService:
    """Email service for sending authentication emails"""

    @staticmethod
    def send_verification_email(email: str, token: str) -> bool:
        """Send email verification email"""
        try:
            if settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(
                    email=email,
                    subject="Verify Your Email Address",
                    template="email_verification",
                    template_data={"verification_token": token}
                )
            else:
                # Fallback for development
                print(f"[EMAIL] Verification email to {email}: token={token}")
                return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False

    @staticmethod
    def send_password_reset_email(email: str, token: str) -> bool:
        """Send password reset email"""
        try:
            if settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(
                    email=email,
                    subject="Reset Your Password",
                    template="password_reset",
                    template_data={"reset_token": token}
                )
            else:
                # Fallback for development
                print(f"[EMAIL] Password reset email to {email}: token={token}")
                return True
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False

    @staticmethod
    def send_account_locked_notification(email: str, lockout_until: str) -> bool:
        """Send account locked notification"""
        try:
            if settings.SENDGRID_API_KEY:
                return EmailService._send_via_sendgrid(
                    email=email,
                    subject="Account Security Alert",
                    template="account_locked",
                    template_data={"lockout_until": lockout_until}
                )
            else:
                print(f"[EMAIL] Account locked notification to {email}: until={lockout_until}")
                return True
        except Exception as e:
            print(f"Error sending account locked notification: {e}")
            return False

    @staticmethod
    def _send_via_sendgrid(
        email: str,
        subject: str,
        template: str,
        template_data: dict,
        retries: int = 3
    ) -> bool:
        """Send email via SendGrid with retry logic"""
        import requests
        import json

        from_email = settings.SENDGRID_FROM_EMAIL
        api_key = settings.SENDGRID_API_KEY

        if not api_key:
            raise ValueError("SendGrid API key not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Simple email body (in production, use SendGrid templates)
        body = {
            "personalizations": [{
                "to": [{"email": email}]
            }],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{
                "type": "text/html",
                "value": EmailService._render_template(template, template_data)
            }]
        }

        for attempt in range(retries):
            try:
                response = requests.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=body,
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [200, 201, 202]:
                    return True
                elif attempt < retries - 1:
                    continue
                else:
                    print(f"SendGrid error: {response.status_code} - {response.text}")
                    return False
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    continue
                else:
                    raise

        return False

    @staticmethod
    def _render_template(template_name: str, data: dict) -> str:
        """Render email template"""
        if template_name == "email_verification":
            token = data.get("verification_token", "")
            return f"""
            <h1>Verify Your Email</h1>
            <p>Click the link below to verify your email address:</p>
            <p><a href="http://localhost:3000/verify-email?token={token}">Verify Email</a></p>
            <p>If you didn't create this account, you can safely ignore this email.</p>
            """

        elif template_name == "password_reset":
            token = data.get("reset_token", "")
            return f"""
            <h1>Reset Your Password</h1>
            <p>Click the link below to reset your password:</p>
            <p><a href="http://localhost:3000/reset-password?token={token}">Reset Password</a></p>
            <p>This link will expire in 30 minutes.</p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            """

        elif template_name == "account_locked":
            lockout_until = data.get("lockout_until", "")
            return f"""
            <h1>Account Security Alert</h1>
            <p>Your account has been locked due to multiple failed login attempts.</p>
            <p>Your account will be unlocked at: {lockout_until}</p>
            <p>If this wasn't you, please reset your password immediately.</p>
            """

        return "<p>Email notification</p>"
