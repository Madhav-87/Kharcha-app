# Budgets and alerts

All endpoints require an active account and bearer access token. Amounts are
integer paise (`₹1.00` is `100`), and budget periods use the first day of a
month (`YYYY-MM-01`). Budget records and expense totals are scoped to the
authenticated user.

## Monthly budget

- `GET /api/v1/budgets/monthly/?period_month=2026-10-01` returns the configured
  limit and paid, non-deleted spend for that month. The current month is used
  when `period_month` is omitted. If no limit is configured, the limit,
  remaining amount, percentage, and recurring flag are `null` while spend is
  still reported.
- `PUT /api/v1/budgets/monthly/` upserts a budget with
  `period_month`, `limit_paise`, and optional `is_recurring`.
- `DELETE /api/v1/budgets/monthly/?period_month=2026-10-01` removes that
  month's budget.

## Category budgets

- `GET /api/v1/budgets/categories/?period_month=2026-10-01` lists the caller's
  category budgets and usage. The current month is the default.
- `POST /api/v1/budgets/categories/` creates a budget with
  `category_public_id`, `period_month`, `limit_paise`, and optional
  `alert_threshold` (1–100) and `is_recurring`. Only one budget per category
  and month is allowed. Categories must be active system categories or owned
  by the caller.
- `GET`, `PATCH`, and `DELETE /api/v1/budgets/categories/{public_id}/` read,
  update the limit/threshold/recurrence, or remove a category budget.

Usage reports `spent_paise`, `remaining_paise` (floored at zero), and
`pct_used`. Spend counts expenses with `status=paid` and no deletion timestamp.

## Alerts

When a monthly budget is reached, the API creates one in-app
`budget_threshold` notification at the user's configured
`budget_alert_threshold` from account settings (80% by default), and one
`budget_exceeded` notification when spend reaches or passes 100%. A category
budget's `alert_threshold` overrides the account threshold; a null value uses
the account threshold. Notifications are deduplicated by budget and month.
They are created only when account settings allow budget alerts. Saving a
budget evaluates existing spend, and manual expense create, update, and delete
operations re-evaluate affected months and categories.
