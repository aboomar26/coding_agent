from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models import TextRequest, TextResponse
import utils

app = FastAPI(
    title="Text Processing API",
    description="API that trims, uppercases, and counts characters/words of input text.",
    version="1.0.0"
)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.post("/process", response_model=TextResponse)
def process_text(payload: TextRequest):
    """Process the input string."""
    try:
        trimmed = utils.trim_text(payload.text)
        uppercase = utils.uppercase_text(trimmed)
        chars = utils.char_count(trimmed)
        words = utils.word_count(trimmed)
        return TextResponse(
            trimmed=trimmed,
            uppercase=uppercase,
            char_count=chars,
            word_count=words
        )
    except ValueError as ve:
        # Re-raise to be caught by handler
        raise ve
    except Exception:
        raise
