FROM astral/uv:python3.11-trixie

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

WORKDIR /chainlit-runtime

CMD ["/bin/bash"]
