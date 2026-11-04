# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --only-group backend --no-install-project
COPY backend ./backend
COPY content ./content
COPY assets/generated ./assets/generated
COPY game/director_contract.py ./game/director_contract.py
COPY game/world_contract.py ./game/world_contract.py
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

COPY game/job_contract.py ./game/job_contract.py

COPY game/i18n.py ./game/i18n.py
COPY web/locale_bridge.js ./web/locale_bridge.js
