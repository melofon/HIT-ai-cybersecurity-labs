Generate uv.lock with `uv sync`

Build the image with `docker buildx build --load -t cybersec-agent-devui .` where:

- `--load` - load the image into local Docker registry
- `-t cybersec-agent-devui` - image tag`
- `.` - path to Dockerfile

