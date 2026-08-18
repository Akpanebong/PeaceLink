import africastalking
from django.conf import settings


def send_sms(phone_number, message):
    try:
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )

        response = africastalking.SMS.send(
            message,
            [phone_number],
            sender_id=settings.AFRICASTALKING_SENDER_ID,
        )

        sms_data = response.get("SMSMessageData", {})
        recipients = sms_data.get("Recipients", [])
        api_message = sms_data.get("Message", "")

        if recipients:
            return {
                "success": True,
                "response": response,
            }

        return {
            "success": False,
            "message": api_message or "SMS was not accepted.",
            "response": response,
        }

    except Exception as exc:
        print(f"Failed to send SMS to {phone_number}")

        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "message": str(exc),
        }