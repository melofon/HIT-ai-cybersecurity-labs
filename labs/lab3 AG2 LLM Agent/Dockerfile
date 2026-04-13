FROM astral/uv:python3.11-trixie

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

CMD ["/bin/bash"]
