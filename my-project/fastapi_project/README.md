# Text Processing API

A simple FastAPI service that receives a string and returns:
- trimmed whitespace
- uppercase version
- character count
- word count

## Installation

```bash
pip install fastapi uvicorn pydantic
```

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at http://localhost:8001

## Example Request

```bash
curl -X POST "http://localhost:8001/process" \
     -H "Content-Type: application/json" \
     -d '{"text": "  Hello, world!  "}'
```

## Example Response

```json
{
  "trimmed": "Hello, world!",
  "uppercase": "HELLO, WORLD!",
  "char_count": 13,
  "word_count": 2
}
```
