# Conversation

```sql
CREATE TABLE IF NOT EXISTS Conversation (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Value guidance:
- No fixed categorical filters are expected. Use `user_id` only when the user asks about chat history.