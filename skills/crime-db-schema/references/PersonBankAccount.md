# PersonBankAccount

```sql
CREATE TABLE IF NOT EXISTS PersonBankAccount (
    person_bank_id TEXT PRIMARY KEY,
    person_id TEXT,
    account_id TEXT,
    relation_type TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES BankAccount(account_id) ON DELETE CASCADE
);
```

Value guidance:
- `relation_type`: `Joint Holder`, `Primary Holder`, `Suspected Beneficiary`