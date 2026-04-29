from pydantic import BaseModel, Field, validator

class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Input string to process")

    @validator('text')
    def not_whitespace(cls, v):
        if not v or v.isspace():
            raise ValueError('text must not be only whitespace')
        return v

class TextResponse(BaseModel):
    trimmed: str
    uppercase: str
    char_count: int
    word_count: int
