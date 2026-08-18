import json
import logging
import re
import urllib.error
import urllib.request

from bs4 import BeautifulSoup, NavigableString
from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction

from core.models import TranslationCache
from core.translations import language_label, phrase_replacements_for

logger = logging.getLogger(__name__)

SKIPPED_TAGS = {"script", "style", "noscript", "code", "pre", "textarea"}
TRANSLATABLE_ATTRS = ("placeholder", "title", "aria-label", "alt")
TEXT_RE = re.compile(r"[A-Za-z\u0600-\u06FF\u00C0-\u024F]")
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def should_translate_text(text):
    stripped = text.strip()
    if not stripped:
        return False
    if not TEXT_RE.search(stripped):
        return False
    return len(stripped) > 1


def translate_html(html, target_language):
    if not target_language or target_language == "en":
        return html

    soup = BeautifulSoup(html, "html.parser")
    text_nodes = []
    attr_refs = []
    source_texts = []

    for node in soup.find_all(string=True):
        parent = node.parent
        if not parent or parent.name in SKIPPED_TAGS:
            continue
        if parent.find_parent(attrs={"data-no-translate": True}) is not None:
            continue
        if "no-translate" in parent.get("class", []):
            continue

        text = str(node)
        if should_translate_text(text):
            text_nodes.append(node)
            source_texts.append(text.strip())

    for tag in soup.find_all(True):
        if tag.name in SKIPPED_TAGS:
            continue
        if tag.find_parent(attrs={"data-no-translate": True}) is not None:
            continue
        if "no-translate" in tag.get("class", []):
            continue
        for attr in TRANSLATABLE_ATTRS:
            value = tag.get(attr)
            if isinstance(value, str) and should_translate_text(value):
                attr_refs.append((tag, attr, value))
                source_texts.append(value.strip())

    translations = translate_many(source_texts, target_language)

    for node in text_nodes:
        original = str(node)
        translated = translations.get(original.strip())
        if translated:
            node.replace_with(NavigableString(original.replace(original.strip(), translated)))

    for tag, attr, original in attr_refs:
        translated = translations.get(original.strip())
        if translated:
            tag[attr] = translated

    return str(soup)


def translate_many(texts, target_language):
    unique_texts = list(dict.fromkeys(text.strip() for text in texts if should_translate_text(text)))
    if not unique_texts or target_language == "en":
        return {}

    cached = get_cached_translations(unique_texts, target_language)
    replacements = phrase_replacements_for(target_language)
    fallback_translations = {
        text: replacements[text]
        for text in unique_texts
        if text not in cached and text in replacements
    }
    missing = [
        text
        for text in unique_texts
        if text not in cached and text not in fallback_translations
    ]

    ai_translations = {}
    for batch in chunk_texts(missing):
        batch_translations = translate_with_ai(batch, target_language)
        if batch_translations:
            save_cached_translations(batch_translations, target_language)
            ai_translations.update(batch_translations)

    return {**cached, **fallback_translations, **ai_translations}


def chunk_texts(texts):
    max_items = getattr(settings, "AI_TRANSLATION_BATCH_ITEMS", 35)
    max_chars = getattr(settings, "AI_TRANSLATION_BATCH_CHARS", 6000)
    batch = []
    char_count = 0

    for text in texts:
        text_length = len(text)
        if batch and (len(batch) >= max_items or char_count + text_length > max_chars):
            yield batch
            batch = []
            char_count = 0

        batch.append(text)
        char_count += text_length

    if batch:
        yield batch


def get_cached_translations(texts, target_language):
    hashes = [TranslationCache.hash_text(text) for text in texts]
    hash_to_text = dict(zip(hashes, texts))

    try:
        rows = TranslationCache.objects.filter(
            target_language=target_language,
            source_hash__in=hashes,
        )
        return {
            hash_to_text[row.source_hash]: row.translated_text
            for row in rows
            if row.source_hash in hash_to_text
        }
    except (OperationalError, ProgrammingError):
        return {}


def save_cached_translations(translations, target_language):
    try:
        with transaction.atomic():
            for source_text, translated_text in translations.items():
                if not translated_text or translated_text == source_text:
                    continue
                TranslationCache.objects.update_or_create(
                    source_hash=TranslationCache.hash_text(source_text),
                    target_language=target_language,
                    defaults={
                        "source_language": "en",
                        "source_text": source_text,
                        "translated_text": translated_text,
                        "provider": "openai",
                    },
                )
    except (OperationalError, ProgrammingError):
        return


def translate_with_ai(texts, target_language):
    api_key = getattr(settings, "AI_TRANSLATION_API_KEY", "")
    if not api_key:
        return {}

    target_label = language_label(target_language)
    endpoint = getattr(settings, "AI_TRANSLATION_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    model = getattr(settings, "AI_TRANSLATION_MODEL", "gpt-4o-mini")

    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are translating text for PeaceLink, a South Sudan peacebuilding and trade platform. "
                    "Translate accurately into the requested target language. Preserve names, numbers, URLs, "
                    "emails, phone numbers, Django-style placeholders, and HTML entities. Return only JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "target_language": target_label,
                        "texts": texts,
                        "response_format": {
                            "translations": [
                                {"source": "original text", "translation": "translated text"}
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=getattr(settings, "AI_TRANSLATION_TIMEOUT", 12)) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        logger.warning("AI translation HTTP error %s: %s", exc.code, detail[:500])
        return {}
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        logger.warning("AI translation failed: %s", exc)
        return {}

    try:
        content = data["choices"][0]["message"]["content"]
        parsed = parse_json_content(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("AI translation response could not be parsed: %s", exc)
        return {}

    translations = {}
    for item in parsed.get("translations", []):
        source = item.get("source")
        translation = item.get("translation")
        if source in texts and isinstance(translation, str):
            translations[source] = translation
    return translations


def parse_json_content(content):
    content = content.strip()
    match = JSON_BLOCK_RE.fullmatch(content)
    if match:
        content = match.group(1).strip()
    return json.loads(content)
