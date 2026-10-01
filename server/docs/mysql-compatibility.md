# MySQL schema and Django model decisions

The supplied `student_finance_schema_mysql.sql` remains the schema authority.
All mapped tables and views use `managed = False`: Django can query them and
write through their models, but migrations must not create or alter them.
Provision the schema, its seed rows, constraints, triggers, and views with the
provided SQL before using application models.

## Field mappings

- `common.db_fields` maps the schema's unsigned `BIGINT`, `INT`, `SMALLINT`,
  and `TINYINT` types, including auto-increment primary keys.
- `PublicIdField` stores UUIDs as dashed text in `CHAR(36)`. Django's built-in
  `UUIDField` uses a different MySQL representation, so it is not used here.
- `FixedCharField`, `VarBinaryField`, and `AsciiBinaryCollationField` preserve
  the schema's `CHAR`, `VARBINARY`, and ASCII bytewise FCM token columns.
- `DateTime3Field` maps to `DATETIME(3)`. Database-current-time defaults and
  ORM-updated timestamps are represented by dedicated field subclasses.
- Money columns remain integer paise. There are no float or decimal money
  fields. JSON columns use Django `JSONField`.
- MySQL `ENUM` columns are represented as `CharField` with `TextChoices` for
  Python validation. The imported schema's ENUM definition enforces the values.
- `MonthlyBudget` and reporting views use Django 5.2 composite primary keys to
  reflect their source row identities.
- The `accounts.User` model maps to `users` and is configured as
  `AUTH_USER_MODEL`. Its password and last-login fields map to `password_hash`
  and `last_login_at`; it adds no columns to the SQL schema.

## Features kept in SQL

Django's model declarations do not fully represent the following MySQL-specific
parts of this design. They must remain present in the supplied SQL and must not
be replaced by generated Django migrations:

- The `expenses` FULLTEXT index.
- The phone, UPI ID, category color, and first-of-month CHECK expressions that
  use MySQL `REGEXP` or date functions. Amount and several budget checks are
  also declared in model state, while the SQL constraints remain authoritative.
- The payment insert/status triggers. They append payment events and synchronize
  linked expense status; payment services must account for these side effects.
- The four reporting views, including the fixed +330 minute conversion used
  for IST reporting.
- Foreign-key delete actions and index definitions from the schema. Django's
  `on_delete` values describe ORM behavior; unmanaged models do not recreate
  the database foreign keys.

## Time handling

Django runs with `USE_TZ = True` and `TIME_ZONE = "UTC"`, matching the schema's
UTC storage convention. The dashboard and analytics views apply the IST offset
for reporting. API serializers should emit aware timestamps and keep money in
integer paise.
