from django.test import TestCase, override_settings

from core.models import TranslationCache
from core import translation_service


class TranslationServiceTests(TestCase):
    @override_settings(AI_TRANSLATION_API_KEY="test-key")
    def test_translate_html_translates_visible_text(self):
        original = translation_service.translate_with_ai

        def fake_translate(texts, target_language):
            return {text: f"SW:{text}" for text in texts}

        translation_service.translate_with_ai = fake_translate
        try:
            html = "<main><h1>Welcome back</h1><p>Market offer from database</p></main>"
            translated = translation_service.translate_html(html, "sw")
        finally:
            translation_service.translate_with_ai = original

        self.assertIn("Karibu tena", translated)
        self.assertIn("SW:Market offer from database", translated)

    @override_settings(AI_TRANSLATION_API_KEY="test-key")
    def test_translate_many_uses_cache_before_ai(self):
        source = "Cached database text"
        TranslationCache.objects.create(
            source_language="en",
            target_language="sw",
            source_hash=TranslationCache.hash_text(source),
            source_text=source,
            translated_text="Maandishi yaliyohifadhiwa",
        )

        original = translation_service.translate_with_ai

        def fail_translate(texts, target_language):
            raise AssertionError("AI should not be called for cached text")

        translation_service.translate_with_ai = fail_translate
        try:
            translations = translation_service.translate_many([source], "sw")
        finally:
            translation_service.translate_with_ai = original

        self.assertEqual(translations[source], "Maandishi yaliyohifadhiwa")

    @override_settings(AI_TRANSLATION_API_KEY="test-key", AI_TRANSLATION_BATCH_ITEMS=2)
    def test_translate_many_batches_missing_texts(self):
        original = translation_service.translate_with_ai
        calls = []

        def fake_translate(texts, target_language):
            calls.append(list(texts))
            return {text: f"SW:{text}" for text in texts}

        translation_service.translate_with_ai = fake_translate
        try:
            translations = translation_service.translate_many(["One", "Two", "Three"], "sw")
        finally:
            translation_service.translate_with_ai = original

        self.assertEqual(len(calls), 2)
        self.assertEqual(translations["One"], "SW:One")
        self.assertEqual(translations["Three"], "SW:Three")

    def test_parse_json_content_handles_fenced_json(self):
        parsed = translation_service.parse_json_content(
            '```json\n{"translations": [{"source": "Hello", "translation": "Habari"}]}\n```'
        )

        self.assertEqual(parsed["translations"][0]["translation"], "Habari")
