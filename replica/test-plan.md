# Validation plan
F01: Save an Arabic named filter preset, persist, filter by publisher, return to All. Test empty/corrupt preferences and explicit secret exclusion.
F02: Group identical headlines from two sources, keep distinct numeric updates separate, preserve all source records, open group view. Empty titles and unrelated-country headlines must not group.
F03: Favorite selected article and verify persisted ID. Existing retention prunes markers with expired articles.
F04: Verify summary counts, unknown dates, empty dataset, overlapping topics and publisher totals. Open all four analytics tabs. Export grouped view and verify all three underlying materials remain in CSV. Escape Excel formula payloads.
Regression: foreign tourism excluded from default relevant view; disabled translation button absent and key never loaded; existing translation/name/credential suites retained; Windows portable self-check preserved.
Windows real Tk integration tests: monitoring/test_listening_desktop.py and monitoring/test_desktop_layout.py. Headless local runtime cannot run Tk, so authoritative GUI execution is Windows GitHub Actions, not a claimed local screenshot review.
