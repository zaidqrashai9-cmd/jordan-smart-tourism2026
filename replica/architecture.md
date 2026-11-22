# Architecture
Preserve Python/Tk and existing feeds. Add listening_tools.py with pure grouping, normalization, summary, preference persistence and CSV escaping helpers. No extra runtime dependency or service. Monitor imports helpers; helpers never import monitor, avoiding circular imports.

Preferences reside in ~/JordanTourismMonitor/listening-preferences.json, separate from encrypted Gemini credentials. Only favorites and named filter values are serialized, via temporary file replacement. Files are per local OS user; no new auth, database or network route. Existing article IDs remain stable. Four-day feed pruning also prunes favorite markers. Saved searches contain configuration only.

Screens follow existing ministry identity. Horizontal/vertical result scrollbars preserve access to all columns. Analytics are a separate resizable tabbed window; snapshot scope is explicitly labeled. All computations use original filtered rows so visual grouping cannot silently reduce reports. Dates use existing publication parser and Jordan timezone; missing dates remain in All, future dates are excluded from trend comparisons.

Build order: helper logic and tests; result filters and preferences; grouped-source review; analytics; Windows integration tests; Windows portable build and smoke check. Existing translation stays disabled with its code intact.

Risks: approximate grouping false positives (optional, all originals retained); free-source coverage gaps (not disguised as reach); dense Windows UI (integration checks at 1000x760 and existing 900x650 regression). No new external APIs or costs.
