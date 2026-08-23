# BankAccount

```sql
CREATE TABLE IF NOT EXISTS BankAccount (
    account_id TEXT PRIMARY KEY,
    bank_name TEXT,
    account_number TEXT UNIQUE,
    ifsc TEXT,
    account_type TEXT
);
```

Value guidance:
- `bank_name`: `Canara Bank`, `HDFC Bank`, `ICICI Bank`, `Karnataka Bank`, `SBI`
- `account_type`: `Current`, `Savings`