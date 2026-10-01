# Analytics and dashboard API

All endpoints require an authenticated, active account. Responses use the standard
`{ "success": true, "data": ..., "message": "" }` envelope. Amounts are integer
paise; dates and month boundaries use India Standard Time (IST).

Analytics are read-only. Spend totals include paid, non-deleted expenses, matching
the MySQL reporting views. The dashboard's recent expense list includes the five
most recently recorded, non-deleted expenses regardless of payment status.

## `GET /api/v1/analytics/dashboard/`

Returns current day/month totals and counts, a zero-filled daily spend trend, the
current monthly budget and category budget usage, the current month's category
breakdown, and five recent expenses.

Query parameter:

- `days` (optional, 1–90; default `7`): number of IST calendar days in the daily
  trend, including today.

## `GET /api/v1/analytics/trends/`

Returns month totals and paid transaction counts, zero-filled for months without
spend.

Query parameter:

- `months` (optional, 1–24; default `6`): number of months ending with the
  current IST month.

## `GET /api/v1/analytics/categories/`

Returns category spend, transaction counts, and share of total spend for a month.

Query parameter:

- `period_month` (optional; defaults to current IST month): ISO date on the first
  day of the month, for example `2026-10-01`.

## `GET /api/v1/analytics/budget-usage/`

Returns the selected month's monthly budget usage (or `null` when no monthly
budget exists) and category budget usage. It accepts the same optional
`period_month` query parameter as the category breakdown.

The summary, category totals, and budget usage are read from the schema's
`v_daily_spend`, `v_category_spend_monthly`, `v_monthly_budget_usage`, and
`v_category_budget_usage` views. These views are schema-owned; Django does not
create or migrate them.
