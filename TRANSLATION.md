# Free Arabic to English editorial translation

Desktop 1.3 adds an editable source and English draft translation window.
The style guide in translation.py is inferred from two user-supplied Petra bilingual examples; this is prompt guidance, not model fine tuning or an official Petra translation.

## One-time Windows setup
1. Install Ollama from https://ollama.com/download/windows
2. Open PowerShell and run: `ollama pull qwen3:8b`
3. Keep Ollama running. In the monitor select a news item and click ترجمة إلى الإنجليزية.
4. Review or paste the COMPLETE Arabic source, then translate. The archive may only have an excerpt. The program translates exactly what is in this editable field.
5. Review the English draft, copy it or save TXT.

No API subscription or OpenAI key. Model download uses internet and several GB disk space. Local generation uses your device and can be slow; 8B may require substantial RAM. No automatic remote fallback. Model generation quality has not been evaluated on this user's physical device. Automated tests cover payload, local endpoint, validation and errors, not linguistic equivalence.

Rules: factual lead; short paragraphs; natural attributed speech; preserve substantive details, numbers and quotation status; do not invent datelines; consistent glossary. Default Imad Hijazin resolves the supplied examples' Imad/Emad inconsistency. No official endorsement. Full-news mode does not intentionally summarize. Unclear names and every number need human review.
