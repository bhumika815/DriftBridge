from app.services.email_service import send_email
from app.services.verification_service import (
    create_verification_code,
    VerificationCooldownError
)


def send_email_verification_code(
    user_id,
    email,
    purpose
):
    """
    Generate a verification code and send it
    to the user's email address.

    Returns:
        tuple[bool, str]

        True, success message when successful.
        False, error message when sending fails
        or the resend cooldown is active.
    """

    try:
        otp, verification_code = create_verification_code(
            user_id=user_id,
            purpose=purpose
        )

    except VerificationCooldownError as error:
        return (
            False,
            str(error)
        )

    subject = "Your DriftBridge verification code"

    body = (
        "Hello,\n\n"
        "Your DriftBridge verification code is:\n\n"
        f"{otp}\n\n"
        "This code will expire in 10 minutes.\n"
        "Do not share this code with anyone.\n\n"
        "If you did not request this code, "
        "you can safely ignore this email.\n\n"
        "DriftBridge"
    )

    email_sent = send_email(
        recipient=email,
        subject=subject,
        body=body
    )

    if not email_sent:
        return (
            False,
            "We could not send the verification email."
        )

    return (
        True,
        "Verification code sent successfully."
    )