FROM node:24-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git python3 python3-pip ripgrep \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN python3 -m pip install --no-cache-dir --break-system-packages .

ENV PYTHONUNBUFFERED=1
EXPOSE 8765
USER node
CMD ["python3", "-m", "coding_executor.server"]
