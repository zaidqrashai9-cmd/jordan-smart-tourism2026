# Arabic to English translation — Windows 1.4

No additional app, Python, Ollama or model download needed. Internet required.

1. Create a Gemini API key at https://aistudio.google.com/apikey and keep the project on Free tier with billing disabled.
2. Select an article in رصد and click ترجمة إلى الإنجليزية.
3. Paste the key in the masked Gemini API key field. It is held only in this process's memory, never saved to feed files, CSV, logs, executable or repository. Re-enter after restarting. Clear it with مسح المفتاح.
4. Review/paste the COMPLETE Arabic text. Stored body may be only an excerpt. Only the visible text is submitted to Google when you click Translate.
5. Click Translate; copy English or save TXT. Try Flash-Lite if Flash is unavailable for your account. No automatic paid fallback or retry loop.

The app cannot verify your Google billing tier. Free availability/quotas depend on your project; keeping billing disabled is essential to avoiding API charges. Google may use free-tier inputs/outputs to improve products. Use published news, not confidential material. Each colleague should use their own key.

STYLE in translation.py retains editorial guidance inferred from the user's two Petra bilingual examples: factual lead; short paragraphs; neutral natural English; explicit attribution; concise honorifics; preserve substantive information, names, numbers and quotation status. Do not invent dates, datelines or absent text; do not silently summarize. This is prompt guidance, not model fine-tuning or an official Petra translation. Imad Hijazin is the default spelling (examples varied Imad/Emad).

Automated mocked API tests cover payload, key in header rather than URL, missing credentials/source, truncation, blocked output and safe quota errors. No real authenticated Gemini request has been tested here because the user's private key stays with the user; linguistic quality and live account quota require user testing.
