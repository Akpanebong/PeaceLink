from django.utils import translation

from core.translation_service import translate_html


class PreferredLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            language = request.user.preferred_language
        else:
            language = request.GET.get("lang") or request.session.get("peacelink_language", "en")
        request.peacelink_language = language
        translation.activate("en")
        request.LANGUAGE_CODE = language
        response = self.get_response(request)
        self.translate_html_response(response, language)
        return response

    def translate_html_response(self, response, language):
        content_type = response.get("Content-Type", "")
        if not content_type.startswith("text/html") or not hasattr(response, "content"):
            return
        if not language or language == "en":
            return
        charset = response.charset or "utf-8"
        html = response.content.decode(charset)
        html = translate_html(html, language)
        response.content = html.encode(charset)
        response["Content-Length"] = str(len(response.content))
