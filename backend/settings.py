import os
from typing import Literal
from pydantic import BaseModel, Field, SecretStr, field_validator

class Settings(BaseModel):
    mode: Literal['mock', 'meta'] = 'mock'
    director_mode: Literal['mock','meta'] = 'mock'
    director_allow_paid_requests: bool = False
    inspector_token: SecretStr = SecretStr('')
    api_key: SecretStr = SecretStr('')
    model: str = Field(default='muse-spark-1.3', min_length=1, max_length=120)
    base_url: str = 'https://api.meta.ai/v1'
    timeout: float = Field(default=25, ge=1, le=30)
    allow_paid_requests: bool = False
    history_pairs: int = Field(default=10, ge=1, le=30)
    max_sessions: int = Field(default=100, ge=1, le=1000)
    session_ttl: float = Field(default=3600, ge=1)

    @field_validator('base_url')
    @classmethod
    def validate_base(cls, value):
        from urllib.parse import urlsplit
        parts = urlsplit(value)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError('API base URL must be HTTPS without credentials or query')
        return value.rstrip('/')

    @classmethod
    def from_env(cls):
        return cls(mode=os.getenv('BUDDY_MODE', 'mock'),
                   director_mode=os.getenv('DIRECTOR_MODE','mock'),
                   director_allow_paid_requests=os.getenv('DIRECTOR_ALLOW_PAID_REQUESTS','false'),
                   inspector_token=os.getenv('ADMIN_TOKEN',''),
                   api_key=os.getenv('MODEL_API_KEY', ''),
                   model=os.getenv('META_MODEL', 'muse-spark-1.3'),
                   base_url=os.getenv('META_API_BASE_URL', 'https://api.meta.ai/v1'),
                   timeout=os.getenv('META_TIMEOUT_SECONDS', '25'),
                   allow_paid_requests=os.getenv('META_ALLOW_PAID_REQUESTS', 'false'),
                   history_pairs=os.getenv('BUDDY_HISTORY_PAIRS', '10'),
                   max_sessions=os.getenv('BUDDY_MAX_SESSIONS', '100'),
                   session_ttl=os.getenv('BUDDY_SESSION_TTL_SECONDS', '3600'))
