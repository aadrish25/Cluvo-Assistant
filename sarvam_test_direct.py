# test_sarvam_direct.py
import asyncio
from backend.services.sarvam import SarvamTranslationLayer

async def main():
    layer = SarvamTranslationLayer()

    result = await layer.translate_text(
        text="How can I help you today?",
        source_lang="en-IN",
        target_lang="hi-IN",
    )
    print("Translate result:", result)

    translated = result.get("translated_text", "")
    if translated:
        print("Translated text:", repr(translated))
        print("Expected Hindi (Devanagari) example for comparison: आप कैसे हैं")
        # Devanagari block is U+0900–U+097F
        # Bengali/Assamese block is U+0980–U+09FF
        # if the printed hex falls in 09xx, Sarvam gave you Bengali/Assamese script
        # despite target_lang="hi-IN" — a real Sarvam-side issue
        # if it's in 09... wait, Devanagari is 09xx too — let me be precise below

asyncio.run(main())