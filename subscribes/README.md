Subscriptions service
=====================

API surface translated to the subscription context from the diagram.

### Domain
- Subscription has `level` (`L` or `M`), `status` (`active`/`canceled`), `expires_at`, optional `pending_level` during level changes.
- Events emitted to outbox/exchange `subscriptions`: created, renewed, cancelled, level change requested, level changed.

### HTTP API
- `POST /subscriptions` — create subscription. Body: `{"level": "L", "expires_at": "<iso-datetime>"}`. Returns created subscription (201).
- `POST /subscriptions/{id}/renew` — extend expiration. Body: `{"expires_at": "<iso-datetime>"}`. Future date must be after current expiration.
- `POST /subscriptions/{id}/cancel` — cancel subscription (200). Clears any pending level change.
- `POST /subscriptions/{id}/level-change/request` — viewer requests level change. Body: `{"target_level": "M"}`.
- `POST /subscriptions/{id}/level-change/apply` — system applies previously requested level change.
- `GET /subscriptions/{id}` — fetch subscription state.

### Events (routing keys)
- `subscription.{id}.created`
- `subscription.{id}.renewed`
- `subscription.{id}.cancelled`
- `subscription.{id}.level-change-requested`
- `subscription.{id}.level-changed`
