import smtplib
from email.mime.text import MIMEText

from .config import FRONTEND_URL, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def send_verification_email(to_email: str, token: str) -> None:
    link = f"{FRONTEND_URL}/verify-email?token={token}"
    body = (
        f"Для подтверждения email перейдите по ссылке:\n\n{link}\n\n"
        "Если вы не регистрировались, проигнорируйте это письмо."
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Подтверждение email — RAG NPA"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.sendmail(SMTP_FROM, to_email, msg.as_string())