import base64
from email.mime.text import MIMEText

import requests
from django.conf import settings
from pascraper.config.base_config import anthropic_client
from pascraper.config.logging_config import configure_logger

logger = configure_logger(__name__)


def send_verification_email(to_email, verification_link):
    html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f8;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <img src="https://your-logo-url.com" alt="ResumeGuru Logo" style="display: block; margin: 0 auto; max-width: 200px;">
        <h2 style="color: #4f46e5;">Welcome to ResumeGuru!</h2>
        <p>Hello,</p>
        <p>Thank you for registering with ResumeGuru. We're excited to have you on board! To get started, please verify your email address by clicking the button below:</p>
        <p style="text-align: center;">
            <a href="{verification_link}" style="background-color: #4f46e5; color: white; padding: 14px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 4px; font-weight: bold; transition: background-color 0.3s;">Verify Your Email</a>
        </p>
        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #4f46e5;">{verification_link}</p>
        <p>If you didn't create an account with ResumeGuru, please ignore this email.</p>
        <p>Best regards,<br>The ResumeGuru Team</p>
    </div>
    <div style="text-align: center; padding-top: 20px; font-size: 12px; color: #666;">
        <p>© 2024 ResumeGuru. All rights reserved.</p>
        <p>
            <a href="#" style="color: #4f46e5; text-decoration: none;">Terms of Service</a> |
            <a href="#" style="color: #4f46e5; text-decoration: none;">Privacy Policy</a>
        </p>
    </div>
</body>
</html>
"""
    return requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data={
            "from": "ResumeGuru Support <support@resumeguru.pro>",
            "to": [to_email],
            "subject": "Verify your email",
            "text": f"Please click this link to verify your email: {verification_link}",
            "html": html_content,
        },
    )


def send_email(to_email, subject, message, html_content, from_email):
    return requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
        auth=("api", settings.MAILGUN_API_KEY),
        data={
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": message,
            "html": html_content,
        },
    )


async def generate_personalized_email(conversation, user_message=None):
    """
    Uses the Anthropic API to generate a personalized email response.
    """
    # Construct the conversation history
    messages = conversation.messages.order_by("sent_at")
    chat_history = []

    for msg in messages:
        if msg.is_incoming:
            chat_history.append({"role": "user", "content": msg.content})
        else:
            chat_history.append({"role": "assistant", "content": msg.content})

    history = "\n".join(chat_history)

    # Create the prompt for the LLM
    prompt = f"""
    Conversation history:
    {history}

    Respond to the user's last message in a helpful and professional manner.
    """

    response = await anthropic_client.completions.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
            {"role": "user", "content": prompt},
            {
                "role": "assistant",
                "content": "You are an assistant for ResumeGuru, helping users with their resume optimization.",
            },
        ],
        max_tokens_to_sample=4096,
        temperature=0.7,
    )

    assistant_message = response.content[0].text

    return assistant_message
