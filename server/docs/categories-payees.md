# Categories and saved payees

All endpoints require an active account and a bearer access token. Responses use
the common `{success, data, message}` envelope. Resource identifiers are UUID
`public_id` values; database IDs are never exposed.

## Categories

- `GET /api/v1/categories/?include_hidden=true` lists system categories and the
  caller's active custom categories. `include_hidden=false` omits categories
  hidden by the caller. Results include base fields and effective icon, color,
  and sort order after personal overrides.
- `POST /api/v1/categories/` creates a custom category. Required fields are
  `name`, `icon`, and `color` (`#RRGGBB`); `emoji` and `sort_order` are optional.
- `GET`, `PATCH`, and `DELETE /api/v1/categories/{public_id}/` read, update, or
  archive a custom category. Delete archives it so existing expense/payment
  references remain valid. System categories cannot be changed or archived.
- `PATCH /api/v1/categories/preferences/` accepts
  `{"preferences":[{"category_public_id":"...","hidden":true,
  "color_override":"#RRGGBB","icon_override":"...","sort_order":1}]}`.
  Each preference field is optional. Categories may be system-wide or owned by
  the caller. Hidden categories remain available to preference management.

## Saved payees

- `GET /api/v1/payees/` lists the caller's saved payees. Optional `search` checks
  name and UPI ID; optional `favorite=true|false` filters favorites. Favorites
  and recently used payees sort first.
- `POST /api/v1/payees/` creates a payee with `name`, `upi_id`, and optional
  `default_category_public_id` and `is_favorite`.
- `GET`, `PATCH`, and `DELETE /api/v1/payees/{public_id}/` read, update, or
  delete a saved payee. UPI IDs must match the schema's `name@handle` format,
  and each user may save a UPI ID only once.

Payee and custom-category reads and writes are scoped to the authenticated user.
A payee's default category must be a system category or one owned by that user.
