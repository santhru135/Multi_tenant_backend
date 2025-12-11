"""
Email service for sending transactional emails.
Uses SMTP with SSL/TLS for secure email delivery.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional, Dict, Any, List
import logging
import jinja2
from pathlib import Path
import os

from config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM_EMAIL
        self.smtp_from_name = settings.SMTP_FROM_NAME
        self.template_dir = Path(__file__).parent.parent / "templates" / "emails"
        
        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=True
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using the specified template or content.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template file (without extension)
            template_data: Data to render the template with
            text_content: Plain text content (alternative to template)
            html_content: HTML content (alternative to template)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if template_data is None:
            template_data = {}
        
        # Add common template variables
        template_data.update({
            "app_name": settings.APP_NAME,
            "support_email": settings.SUPPORT_EMAIL,
            "frontend_url": settings.FRONTEND_URL,
            "now": datetime.now()  # Add current datetime for templates
        })
        
        # Render templates if not provided
        if not (text_content and html_content):
            try:
                text_template = self.template_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**template_data)
                
                try:
                    html_template = self.template_env.get_template(f"{template_name}.html")
                    html_content = html_template.render(**template_data)
                except jinja2.TemplateNotFound:
                    html_content = None
                    
            except Exception as e:
                logger.error(f"Error rendering email template: {str(e)}")
                return False
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((self.smtp_from_name, self.smtp_from))
        msg['To'] = to_email
        
        # Attach parts
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
        
        # Send the email
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
                logger.info(f"Email sent to {to_email} with subject: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
        user_name: str = "User"
    ) -> bool:
        """Send password reset email"""
        return await self.send_email(
            to_email=email,
            subject=f"{settings.APP_NAME} - Password Reset",
            template_name="password_reset",
            template_data={
                "user_name": user_name,
                "reset_link": reset_link,
                "expiry_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
            }
        )
    
    async def send_account_verification_email(
        self,
        email: str,
        verification_link: str,
        user_name: str = "User"
    ) -> bool:
        """Send account verification email"""
        return await self.send_email(
            to_email=email,
            subject=f"{settings.APP_NAME} - Verify Your Email",
            template_name="verify_email",
            template_data={
                "user_name": user_name,
                "verification_link": verification_link
            }
        )
    
    async def send_welcome_email(
        self,
        email: str,
        user_name: str = "User"
    ) -> bool:
        """Send welcome email to new users"""
        return await self.send_email(
            to_email=email,
            subject=f"Welcome to {settings.APP_NAME}!",
            template_name="welcome",
            template_data={
                "user_name": user_name,
                "login_url": f"{settings.FRONTEND_URL}/login",
                "support_email": settings.SUPPORT_EMAIL
            }
        )

# Singleton instance
email_service = EmailService()
