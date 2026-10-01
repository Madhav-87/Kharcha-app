# Manual expenses and filtering

All endpoints require an active account and bearer access token. Expense
identifiers in requests and responses use UUID `public_id` values. Amounts are
integer paise (`₹1.00` is `100`).

## Create and manage an expense

- `POST /api/v1/expenses/` creates a manual expense. Required fields are
  `title`, `amount_paise`, and `category_public_id`. Optional fields are
  `payee_public_id`, `note`, `method`, `status`, and ISO-8601 `expense_at`.
  Method defaults to `upi`; status defaults to `paid`; source is always
  `manual` for this endpoint. Categories must be active system categories or
  owned by the caller. A linked payee must belong to the caller.
- `GET /api/v1/expenses/{public_id}/` reads an expense owned by the caller.
- `PATCH /api/v1/expenses/{public_id}/` updates a manual expense.
- `DELETE /api/v1/expenses/{public_id}/` soft-deletes a manual expense.

Payment-linked expenses can be read and filtered with the list endpoint. Their
state is managed by payment processing, so they cannot be edited or deleted
through the manual expense endpoints.

## Filtering and pagination

`GET /api/v1/expenses/` accepts these optional query parameters:

| Parameter | Meaning |
| --- | --- |
| `search` | Case-insensitive match in title, note, or saved payee name |
| `category_public_id` | Filter by category UUID |
| `status` | `paid`, `pending`, or `failed` |
| `method` | `upi`, `cash`, `card`, `netbanking`, or `other` |
| `source` | `manual` or `upi_payment` |
| `date_from`, `date_to` | Inclusive ISO calendar dates, such as `2026-09-01` |
| `min_amount_paise`, `max_amount_paise` | Inclusive amount range |
| `ordering` | `-expense_at` (default), `expense_at`, `-amount_paise`, `amount_paise`, or `title` |
| `page` | Page number, starting at 1 |
| `page_size` | Results per page, from 1 to 100; defaults to 20 |

The response `data` contains `results` and `pagination` (`page`, `page_size`,
`total`, `total_pages`, `has_next`, and `has_previous`). Deleted expenses are
excluded. All filtering is applied within the caller's expenses.
