# REST API Rate Limits and Authentication Guidelines

## 1. Rate Limit Thresholds
All API requests are authenticated via Bearer tokens or verified API keys.
- **Standard Tier:** 1,000 requests per minute per organization token.
- **Enterprise Tier:** 10,000 requests per minute with burst capacity up to 20,000 RPM.

## 2. Handling HTTP 429 Too Many Requests
When an API client exceeds the allowable rate limit, the API gateway returns an `HTTP 429 Too Many Requests` status code with a `Retry-After` header specifying the number of seconds to wait.

## 3. Webhook Idempotency
Clients consuming webhook event notifications should utilize the `event_id` or `idempotency_key` headers to safely deduplicate repeated deliveries. Duplicate events received within 24 hours are safely acknowledged without re-processing.
