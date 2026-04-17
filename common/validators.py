from datetime import date
from rest_framework.exceptions import ValidationError


def validate_user_age_from_token(request):
    token = request.auth

    if token is None:
        raise ValidationError("Authentication required.")

    birthdate_str = None

    if hasattr(token, "get"):
        birthdate_str = token.get("birthdate")
    elif hasattr(token, "payload"):
        birthdate_str = token.payload.get("birthdate")

    if not birthdate_str:
        raise ValidationError("Укажите дату рождения, чтобы создать продукт.")

    try:
        if isinstance(birthdate_str, str):
            birthdate = date.fromisoformat(birthdate_str)
        else:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError("Invalid birthdate format in token.")

    today = date.today()
    age = (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )

    if age < 18:
        raise ValidationError("Вам должно быть 18 лет, чтобы создать продукт.")
