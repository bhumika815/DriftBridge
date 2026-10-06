import secrets
from datetime import datetime, timedelta

from app import db, bcrypt
from app.models.verification import VerificationCode


OTP_LENGTH = 6
OTP_EXPIRATION_MINUTES = 10
MAX_OTP_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


VERIFICATION_PURPOSE_SIGNUP_EMAIL = "SIGNUP_EMAIL"
VERIFICATION_PURPOSE_CHANGE_EMAIL = "CHANGE_EMAIL"
VERIFICATION_PURPOSE_CHANGE_PASSWORD = "CHANGE_PASSWORD"
VERIFICATION_PURPOSE_VERIFY_EMAIL = "VERIFY_EMAIL"
VERIFICATION_PURPOSE_RESET_PASSWORD = "RESET_PASSWORD"


class VerificationCooldownError(Exception):
    """
    Raised when a new OTP is requested before
    the resend cooldown has finished.
    """

    pass


def generate_otp():
    """
    Generate a cryptographically secure numeric OTP.
    """

    return "".join(
        str(secrets.randbelow(10))
        for _ in range(OTP_LENGTH)
    )


def create_verification_code(
    user_id,
    purpose,
    expiration_minutes=OTP_EXPIRATION_MINUTES
):
    """
    Generate and store a new verification code.

    Only one active verification code is allowed
    for the same user and purpose.

    Returns:
        tuple[str, VerificationCode]
        The plain OTP and the stored verification record.

    Raises:
        VerificationCooldownError:
            If a new OTP is requested too soon.
    """

    now = datetime.utcnow()

    latest_code = (
        VerificationCode.query
        .filter_by(
            user_id=user_id,
            purpose=purpose,
            used=False
        )
        .order_by(
            VerificationCode.created_at.desc()
        )
        .first()
    )

    if latest_code is not None:

        seconds_since_creation = (
            now - latest_code.created_at
        ).total_seconds()

        if seconds_since_creation < OTP_RESEND_COOLDOWN_SECONDS:
            remaining_seconds = int(
                OTP_RESEND_COOLDOWN_SECONDS
                - seconds_since_creation
            )

            raise VerificationCooldownError(
                f"Please wait {remaining_seconds} "
                "seconds before requesting another code."
            )

    (
        VerificationCode.query
        .filter_by(
            user_id=user_id,
            purpose=purpose,
            used=False
        )
        .update(
            {
                VerificationCode.used: True
            },
            synchronize_session=False
        )
    )

    otp = generate_otp()

    code_hash = bcrypt.generate_password_hash(
        otp
    ).decode("utf-8")

    expires_at = (
        now
        + timedelta(minutes=expiration_minutes)
    )

    verification_code = VerificationCode(
        user_id=user_id,
        purpose=purpose,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0,
        used=False
    )

    db.session.add(verification_code)
    db.session.commit()

    return otp, verification_code


def verify_code(
    user_id,
    purpose,
    otp
):
    """
    Verify an OTP for a specific user and purpose.

    Returns:
        tuple[bool, str]
        A success flag and a message describing the result.
    """

    verification_code = (
        VerificationCode.query
        .filter_by(
            user_id=user_id,
            purpose=purpose,
            used=False
        )
        .order_by(
            VerificationCode.created_at.desc()
        )
        .first()
    )

    if verification_code is None:
        return (
            False,
            "No active verification code was found."
        )

    if datetime.utcnow() > verification_code.expires_at:

        verification_code.used = True

        db.session.commit()

        return (
            False,
            "This verification code has expired."
        )

    if verification_code.attempts >= MAX_OTP_ATTEMPTS:

        verification_code.used = True

        db.session.commit()

        return (
            False,
            "Too many incorrect attempts."
        )

    verification_code.attempts += 1

    if not bcrypt.check_password_hash(
        verification_code.code_hash,
        otp
    ):
        db.session.commit()

        return (
            False,
            "Invalid verification code."
        )

    verification_code.used = True

    db.session.commit()

    return (
        True,
        "Verification successful."
    )