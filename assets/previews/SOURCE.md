# Portfolio interface excerpts

Captured locally on 20 October 2026 from the existing RU/EN portfolio mockups and
demos. Base Git revision: `7d03e03f68957365fd28398810f1fb124c7aaec8`.
The current uncommitted portfolio polish changes their surrounding presentation,
not the demo product code. These are not production account screenshots.

| Files, including `-en` variants | Local source | Captured state |
|---|---|---|
| `scout.jpg` | `case-scout.html`, `.sc-window`; EN `.visual .window` | Existing interface mockup, fictional companies and numbers |
| `subscriptions.jpg` | `case-subscriptions.html`, `.sub-state + div > div` | `/start` and mock tariff selection, no payment |
| `crm.jpg` | `case-crm.html`, `.crm-network` | Existing scripted contact graph, fictional people |
| `vetpulse.jpg` | `case-vetpulse.html`, demo chat | First scripted request and response, fictional clinic data |
| `autopricer.jpg` | `case-autopricer.html`, `.pnl-wrap` | Default synthetic price calculation, not marketplace records |
| `mutual.jpg` | `case-mutual.html`, `.ph-fit__in` | Nearby screen after default privacy settings, fictional profiles/map |
| `faith.jpg` | `case-faith.html`, `.ph-fit__in` | Web lesson excerpt, not the installed Flutter application or expert acceptance |

`tools/build-project-previews.cjs` reproduces the capture using an existing
Playwright/Chrome installation. It permits only local GET requests, rejects
external traffic, and stores JPEG excerpts at 1.5 device scale and quality 83.
Portrait interfaces are intentionally shown as excerpts; no features are added.
Set `REDND_PREVIEW_ONLY` to a comma-separated scene list to update only those
derivatives. Review output visually before changing the portfolio references.

The existing Chainya public catalogue and KREM setup images remain in
`assets/cases/`; their originals are unchanged. No new cross-project copies,
customer records, credentials, account sessions, payments or real messages were
used. Separate OG images remain the social-sharing assets, not interface previews.
