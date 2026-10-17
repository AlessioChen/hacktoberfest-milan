FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
COPY data ./data
COPY assets ./assets
COPY .streamlit ./.streamlit
ENV PATH="/srv/.venv/bin:$PATH" DB_PATH=/db/frigo.db SHELF_LIFE_PATH=/srv/data/shelf_life.yaml
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
