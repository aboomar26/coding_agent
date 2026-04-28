# Text Processing Service

Run the service with:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API provides a POST endpoint at `/process` that accepts JSON with:
- `text` (required, non-empty string)
- `language` (optional string)
- `max_length` (optional positive integer)

It returns the processed text (uppercased, optionally truncated), original length, and word count.
