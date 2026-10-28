FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir pygbag==0.9.3
COPY tools/package_web.py tools/build_web.py ./tools/
ENV CHESS_CORP_RUNTIME_CACHE=/opt/chess-runtime
RUN python tools/build_web.py --fetch-runtime
COPY main.py ./
COPY game ./game
COPY content ./content
COPY assets/processed ./assets/processed
COPY web ./web
RUN python tools/build_web.py

FROM nginx:stable-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/web_app/build/web/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
