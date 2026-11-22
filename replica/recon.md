# Public-product recon: Brand24 patterns for Rasd
Date: 2026-11-22. Platform: existing Windows Tk desktop. Audience: Jordan Ministry of Tourism media unit.
Scope authorized by user: improve existing Jordan tourism monitoring using applicable Brand24 functionality; no change to discovery, relevance gates, retention, time/language/sentiment filters or disabled translation.

## Sources
| Source | URL | Evidence |
| --- | --- | --- |
| Features | https://brand24.com/features/ | Analysis, topics, volume trends, exports, filters |
| Dashboard documentation | https://help.brand24.com/en/collections/10259546-dashboard | Sources, saved filters, summary and analysis |
| Saved filters | https://help.brand24.com/en/articles/9790756-saved-filters | Name, save and select filter presets |
| Mentions overview | https://help.brand24.com/en/articles/9772539-mentions-tab-overview | Mentions list, charts, filters and editorial actions |
| Summary overview | https://help.brand24.com/en/articles/3325991-summary-tab-overview | Counts, source distribution and period comparisons |

Only public documentation was read. No signed-in session, source bundles, private APIs, brand assets or proprietary algorithms used. Brand24 internals are unknown. Features below are fresh implementations; grouping is an independent improvement rather than a claimed Brand24 algorithm.

## Core loop
Collect Jordan tourism news, filter it, inspect and organize the relevant materials, analyze the filtered selection and export/share it for editorial review.

## Screen inventory
| ID | Screen | Entry | Components | States |
| --- | --- | --- | --- | --- |
| S01 | Results | startup | Existing filters plus source selector, saved search selector, grouping and favorites switches, scrollable result table | empty, populated, updating, cached error, unknown dates |
| S02 | Analytics snapshot | Analysis button | Total materials, approximate unique stories, source counts, date histogram, sentiment table, rule-based topics | empty, dated/undated, constrained filter, limited comparison history |
| S03 | Similar materials | Sources button | All grouped materials and source opener | no selection, singleton, multiple sources |
| S04 | Saved search name | Save search | Name input, overwrite question | cancelled, empty, new, existing |

## Flows
F01 Filter relevant results by date, language, impact, keyword and source; save named preset; select it later; optionally delete it.
F02 Enable approximate title grouping, inspect all materials in a group and open the selected source. Disable grouping to restore raw results.
F03 Toggle a selected material's favorite marker, view only favorites, persist locally. Markers expire with the four-day archive.
F04 Open an analytics snapshot of all matching raw materials; inspect date, sources, sentiment and topics. Export CSV preserves all matching materials even when grouped.

## Data model (our design; not inferred Brand24 backend)
Article: existing id, title, source, url, published, summary, body. Existing feed schema unchanged.
Preferences: favorites [article IDs], searches {name: filter settings}. Per Windows profile; no team sync.
StoryGroup: transient list of article records, newest record is representative. Never deletes or mutates raw feed.
Analytics: transient snapshot, counts derived from current raw filter matches, not from collapsed view.

## Limits
No Brand24 data sources, reach/engagement estimates, proprietary AI, accounts, paid integrations or social collection added. No claim of comprehensive coverage. Sentiment/relevance code unchanged. Topic labels are rules, may overlap. Grouping is same-language conservative headline similarity, not cross-language semantic deduplication. Volume comparison is descriptive and may reflect collection changes.
Size: incremental desktop slice; 4 screens, 4 flows, 2 existing/new persistent record types. Hard parts: conservative grouping, filter consistency, small-window usability. No perfect parity claim.
