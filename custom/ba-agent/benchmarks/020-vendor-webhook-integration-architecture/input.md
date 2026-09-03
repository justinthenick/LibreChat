# Benchmark 020 — Vendor SaaS Webhook-to-Polling Integration Architecture

## User objective

The user wants new and updated inspection records from a vendor-hosted SaaS platform to appear automatically in an internal work-management system within roughly **10 minutes**, without manual export/import work.

Their first implementation idea is: **“Configure a webhook in the vendor SaaS so every record change is posted directly into our internal system.”**

Do not reject the automation outcome merely because that exact mechanism is unavailable. If direct webhook delivery is not possible, design the smallest maintainable architecture that achieves the outcome from the supplied capabilities.

Do not browse the web. Treat the supplied evidence below as authoritative.

## Supplied vendor SaaS evidence

- The SaaS provides an authenticated HTTPS REST API.
- Authentication uses OAuth 2.0 client credentials.
- `GET /records` lists inspection records.
- `GET /records/{id}` retrieves one record.
- `GET /records` supports an `updated_since` ISO timestamp filter.
- Every record has a stable `record_id` and an `updated_at` timestamp.
- The SaaS provides **no outbound webhook/event/subscription feature** for record changes.
- The SaaS provides no user-configurable mechanism that can POST directly to another system when a record changes.
- A scheduled CSV export exists, but it runs at most once per hour.
- The published API rate limit and expected record-change volume are **not supplied** in this packet.

## Supplied internal-system evidence

- The internal work-management system exposes an authenticated HTTPS REST API.
- Its API can create or update mirror records using a supplied external identifier.
- It supports idempotent upsert using the vendor `record_id` as `external_id`.
- The internal API is reachable from the corporate LAN but is not exposed as a general public internet endpoint.

## Available runtime / network evidence

- An existing always-on Linux VM/container host is available inside the corporate LAN.
- That host can make outbound HTTPS requests to the vendor SaaS.
- That host can reach the internal work-management API.
- The user accepts polling if changes normally arrive within about 10 minutes.
- No additional hardware purchase is required merely to host a lightweight integration worker.
- Browser automation/RPA is not preferred when an API-based approach is available.

## Operational preferences

- Prefer a maintainable service over fragile scraping or UI automation.
- Avoid duplicate records when a poll is repeated after a failure.
- Failed synchronization should be observable and recoverable rather than silently losing changes.
- Credentials must not be embedded in source code; the exact enterprise secret-management mechanism is not supplied.

## Important benchmark boundaries

- Do not invent a webhook or event endpoint that is not in the evidence.
- Do not invent a vendor API rate limit, transaction volume, retry interval, queue technology, database product, cloud platform or secret-management product.
- Do not claim that a particular polling interval is safe until rate-limit/volume adequacy is verified.
- Do not jump to product procurement; the evidence already provides a suitable runtime host.
