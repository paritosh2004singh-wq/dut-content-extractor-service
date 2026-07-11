from pydantic import BaseModel, ConfigDict
import re

class DocumentHash(BaseModel):
    model_config = ConfigDict(frozen=True)
    hash_value: str

    @classmethod
    def validate_hash(cls, v: str) -> str:
        if not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError('Invalid SHA-256 hash')
        return v

class PageNumber(BaseModel):
    model_config = ConfigDict(frozen=True)
    number: int

    @classmethod
    def validate_number(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Page number must be positive')
        return v
