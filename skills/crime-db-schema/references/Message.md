# Message

```sql
CREATE TABLE IF NOT EXISTS Message (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    sender TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES Conversation(conversation_id) ON DELETE CASCADE
);
```

Value guidance:
- `sender`: `assistant`, `user`