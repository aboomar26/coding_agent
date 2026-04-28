from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import Optional

app = FastAPI()

class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Optional[str] = None
    max_length: Optional[int] = Field(None, gt=0)

    @validator('text')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('text must be non-empty')
        return v

@app.post("/process")
async def process(request: ProcessRequest):
    text = request.text
    if request.max_length is not None:
        text = text[:request.max_length]
    processed = text.upper()
    original_length = len(request.text)
    word_count = len(request.text.split())
    return {
        "processed_text": processed,
        "original_length": original_length,
        "word_count": word_count
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return {"error": "Internal server error"}, 500
