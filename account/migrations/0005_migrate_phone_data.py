from django.db import migrations


def forwards(apps, schema_editor):
    """Copy existing country_code + phone into the phone field as an E.164 string.

    This migration expects the current database still has the old `country_code` (TextChoice)
    and `phone` (char) columns from earlier migrations. It will combine them into
    an international phone string and store it in the `phone` column so that
    subsequent schema migrations that remove `country_code` won't lose data.
    """
    phonenumbers = None
    try:
        import phonenumbers
        from phonenumbers import PhoneNumberFormat
    except Exception:
        phonenumbers = None

    Profile = apps.get_model("account", "Profile")
    for p in Profile.objects.all():
        try:
            cc = getattr(p, "country_code", None) or ""
            ph = getattr(p, "phone", None) or ""
            # normalize digits
            digits = "".join(ch for ch in ph if ch.isdigit())
            if not digits:
                # nothing to copy
                continue

            if cc:
                code_digits = str(cc).lstrip("+")
                if digits.startswith(code_digits):
                    candidate = f"+{digits}"
                else:
                    candidate = f"{cc}{digits.lstrip('0')}"
            else:
                candidate = f"+{digits}"

            # If phonenumbers library is available, try to parse and format
            if phonenumbers:
                try:
                    num = phonenumbers.parse(candidate, None)
                    if phonenumbers.is_valid_number(num):
                        candidate = phonenumbers.format_number(num, PhoneNumberFormat.E164)
                except Exception:
                    # Leave candidate as-is if parsing fails
                    pass

            # Assign back to the phone field. The model may change later to PhoneNumberField
            p.phone = candidate
            p.save(update_fields=["phone"])

        except Exception:
            # don't fail migration for single-row issues
            continue


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0004_alter_profile_preferred_language"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
