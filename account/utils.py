import secrets
import string
import phonenumbers
from phonenumbers import geocoder


def generate_strong_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_country_choices():
    choices = []

    for region in phonenumbers.SUPPORTED_REGIONS:
        try:
            country_code = phonenumbers.country_code_for_region(region)

            if not country_code:
                continue

            country_name = geocoder.country_name_for_number(
                phonenumbers.PhoneNumber(
                    country_code=country_code,
                    national_number=0
                ),
                "en"
            )

            if not country_name:
                country_name = region

            choices.append(
                (
                    region,
                    f"{country_name} (+{country_code})"
                )
            )

        except Exception:
            continue

    return sorted(
        choices,
        key=lambda item: item[1]
    )