# رصد وحدة الاعلام — native iPhone 2.0

A SwiftUI iPhone application, independent of the earlier WebView clients. Requires iOS 17+.

## What works

News, all desktop filters, direct on-phone RSS search, shared hourly-target collection, an offline cache, article details, classification explanations, native sharing including WhatsApp, clipboard, JSON import/export, Arabic CSV export, and a separate social tab with local manual-post entry.

The locality directory contains all 958 numeric locality rows and 12 governorate records from Jordan Department of Statistics' bilingual 2025 locality workbook. It preserves combined locality rows and does not mislabel every locality as a city. Source and workbook SHA-256 are included in `Resources/localities.json`. Administrative names are geographic evidence only when tourism relevance and Jordan disambiguation are established.

## News collection

`monitoring/collect.py` generates the shared public-news feed at `data/news.json`. GitHub Actions targets hourly collection at minute 17. GitHub can delay runs and can disable inactive public-repository schedules. The iPhone's direct search runs a rotating batch without requiring a server trigger or personal GitHub token.

The first bundle contains real collected news, not demo items. Google News discovery is currently connected. Source failures and query counts are visible. High recall is a target, not a guarantee of every publication. Text extraction is attempted on a bounded number of articles per server run. The shared feed publishes an excerpt, entity matches and estimated labels, not a mirror of full copyrighted articles. Locally imported full text stays on the phone.

## Social coverage

Facebook, Instagram and X are NOT connected until authorized API access is configured and a request succeeds. Manual public-post entry works and stays on the device. Environment-secret adapters are implemented in the collector:

- `META_ACCESS_TOKEN`, `META_GRAPH_VERSION`, `FACEBOOK_PAGE_ID` for authorized Facebook Page posts.
- `META_ACCESS_TOKEN`, `META_GRAPH_VERSION`, `INSTAGRAM_ACCOUNT_ID` for authorized account media.
- `X_BEARER_TOKEN` for the configured recent-search query, subject to the account's API entitlement and limits.

These adapters have no live authorization in this project; current API access and permissions must be verified before activation. No passwords or tokens are shipped in the iPhone app. Private/social manual imports are never committed to the public feed.

## Build on macOS

1. Install Xcode and XcodeGen.
2. In `ios/`, run `xcodegen generate`.
3. Open `MediaMonitor.xcodeproj`.
4. Choose the MediaMonitor scheme and an iPhone simulator, then Run.
5. For your real iPhone, set your own Apple signing team locally. Never send your Apple password to a chat or commit signing credentials.

GitHub Actions builds and tests the simulator version and creates `MediaUnitMonitor-unsigned.ipa` for an actual iPhone CPU. **Unsigned means it is not directly installable from Safari.** It must be signed with an appropriate Apple provisioning profile, locally using Xcode or a compatible personal-device signing tool. TestFlight/App Store distribution needs the appropriate Apple Developer membership and review process.

## Windows / personal-device testing

AltStore Classic is one available personal-device signing route on Windows. Follow its current official instructions: https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows . Import the generated unsigned IPA through the supported local signing flow. Free personal-team provisioning is temporary and normally needs renewal after seven days. This route is not equivalent to App Store distribution, and it has not been tested on the owner's physical phone here.

## Retention and privacy

Items expire from display after 96 hours from original publication, or first discovery only when publication is unknown. Local files are pruned when the app runs; the phone cannot perform cleanup while powered off. Shared storage is pruned on collection runs. Unknown publication dates do not appear in exact publication-time windows. Sharing always requires the user's recipient selection and confirmation.

## Verification

Unit tests cover Amman dates, rolling windows, expiry, name/country disambiguation, body-only keyword matches, unknown dates and the complete bilingual directory. UI tests open native news, filters, social and source screens. GitHub artifacts include an actual simulator screenshot and test results. No signed physical-device installation or live social authorization is claimed by these tests.
