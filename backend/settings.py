import os
from typing import Literal
from pydantic import BaseModel, Field, SecretStr, field_validator

class Settings(BaseModel):
    mode: Literal['mock', 'meta'] = 'mock'
    director_mode: Literal['mock','meta'] = 'mock'
    director_allow_paid_requests: bool = False
    world_ai_mode: Literal['mock','meta'] = 'mock'
    world_ai_allow_paid_requests: bool = False
    world_ai_session_limit: int = Field(default=3,ge=1,le=100)
    world_ai_global_limit: int = Field(default=3,ge=1,le=1000)
    world_ai_min_interval_seconds: float = Field(default=30,ge=20,le=120)
    world_ai_max_output_tokens: int = Field(default=1800,ge=512,le=4096)
    world_ai_token_budget: int = Field(default=50000,ge=1000,le=5000000)
    world_ai_ledger_path: str = ''
    session_jobs_global_limit: int = Field(default=50,ge=1,le=1000)
    asset_ai_mode: Literal['mock','meta'] = 'mock'
    asset_ai_allow_paid_requests: bool = False
    asset_ai_global_limit: int = Field(default=1,ge=1,le=1000)
    asset_ai_timeout_seconds: float = Field(default=120,ge=10,le=180)
    asset_cache_dir: str = Field(default_factory=lambda:os.getenv('ASSET_AI_CACHE_DIR',str(__import__('pathlib').Path(__file__).resolve().parent.parent/'assets/generated')))
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
        return cls(session_jobs_global_limit=os.getenv('SESSION_JOBS_GLOBAL_LIMIT','50'),world_ai_ledger_path=os.getenv('WORLD_AI_LEDGER_PATH',''),asset_ai_mode=os.getenv('ASSET_AI_MODE','mock'),
                   asset_ai_allow_paid_requests=os.getenv('ASSET_AI_ALLOW_PAID_REQUESTS','false'),
                   asset_ai_global_limit=os.getenv('ASSET_AI_GLOBAL_LIMIT','1'),
                   asset_ai_timeout_seconds=os.getenv('ASSET_AI_TIMEOUT_SECONDS','120'),
                   mode=os.getenv('BUDDY_MODE', 'mock'),
                   director_mode=os.getenv('DIRECTOR_MODE','mock'),
                   director_allow_paid_requests=os.getenv('DIRECTOR_ALLOW_PAID_REQUESTS','false'),
                   world_ai_mode=os.getenv('WORLD_AI_MODE','mock'),
                   world_ai_allow_paid_requests=os.getenv('WORLD_AI_ALLOW_PAID_REQUESTS','false'),
                   world_ai_session_limit=os.getenv('WORLD_AI_SESSION_LIMIT','3'),
                   world_ai_global_limit=os.getenv('WORLD_AI_GLOBAL_LIMIT','3'),
                   world_ai_min_interval_seconds=os.getenv('WORLD_AI_MIN_INTERVAL_SECONDS','30'),
                   world_ai_max_output_tokens=os.getenv('WORLD_AI_MAX_OUTPUT_TOKENS','1800'),
                   world_ai_token_budget=os.getenv('WORLD_AI_TOKEN_BUDGET','50000'),
                   inspector_token=os.getenv('ADMIN_TOKEN',''),
                   api_key=os.getenv('MODEL_API_KEY', ''),
                   model=os.getenv('META_MODEL', 'muse-spark-1.3'),
                   base_url=os.getenv('META_API_BASE_URL', 'https://api.meta.ai/v1'),
                   timeout=os.getenv('META_TIMEOUT_SECONDS', '25'),
                   allow_paid_requests=os.getenv('META_ALLOW_PAID_REQUESTS', 'false'),
                   history_pairs=os.getenv('BUDDY_HISTORY_PAIRS', '10'),
                   max_sessions=os.getenv('BUDDY_MAX_SESSIONS', '100'),
                   session_ttl=os.getenv('BUDDY_SESSION_TTL_SECONDS', '3600'))
