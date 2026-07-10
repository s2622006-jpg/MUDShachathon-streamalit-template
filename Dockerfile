FROM python:3.14-slim

# uv 本体を公式イメージからコピーして使う（pip install不要で高速）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# 依存関係の定義だけ先にコピーし、Dockerのレイヤーキャッシュを効かせる
# （アプリのコードだけ変更した場合、pip installをやり直さずに済む）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# アプリ本体をコピー
COPY . .
RUN uv sync --frozen

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
