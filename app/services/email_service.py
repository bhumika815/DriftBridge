import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(
    recipient,
    subject,
    body
):
    """
    Send an email using the application's SMTP configuration.

    Returns:
        True if the email was sent successfully.
        False if sending failed.
    """

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = current_app.config["MAIL_FROM"]
    message["To"] = recipient

    message.set_content(body)

    try:
        with smtplib.SMTP(
            current_app.config["MAIL_SERVER"],
            current_app.config["MAIL_PORT"]
        ) as smtp:

            if current_app.config["MAIL_USE_TLS"]:
                smtp.starttls()

            smtp.login(
                current_app.config["MAIL_USERNAME"],
                current_app.config["MAIL_PASSWORD"]
            )

            smtp.send_message(message)

        return True

    except Exception as error:
        current_app.logger.exception(
            "Failed to send email: %s",
            error
        )

        return False