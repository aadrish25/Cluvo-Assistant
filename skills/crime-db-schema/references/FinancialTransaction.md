# FinancialTransaction

```sql
CREATE TABLE IF NOT EXISTS FinancialTransaction (
    transaction_id TEXT PRIMARY KEY,
    from_account_id TEXT,
    to_account_id TEXT,
    amount REAL,
    transaction_date TEXT,
    transaction_type TEXT,
    remarks TEXT,
    FOREIGN KEY (from_account_id) REFERENCES BankAccount(account_id),
    FOREIGN KEY (to_account_id) REFERENCES BankAccount(account_id)
);
```

Value guidance:
- `transaction_type`: `Cash Deposit`, `IMPS`, `NEFT`, `UPI`
- `remarks`: commonly `goods`, `loan repayment`, `advance`, `personal transfer`