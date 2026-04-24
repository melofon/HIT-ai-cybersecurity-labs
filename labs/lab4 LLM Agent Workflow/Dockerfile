FROM astral/uv:python3.11-trixie

WORKDIR /app

# Dependencies are declared in pyproject.toml.
COPY pyproject.toml ./
RUN UV_PROJECT_ENVIRONMENT=/usr/local uv sync --no-dev --no-install-project

# Chainlit runs from a container-only runtime directory so .chainlit and .files
# are not created in the mounted source tree.
WORKDIR /chainlit-runtime

CMD ["/bin/bash"]
