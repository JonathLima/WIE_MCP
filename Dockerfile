FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Obscura stealth headless browser (Rust) — the anti-bot fallback tier.
# "no-render-stealth" = V8 JS + live DOM + TLS impersonation (BoringSSL), no visual
# renderer. Extracts "obscura" and "obscura-worker" into /usr/local/bin.
# System dependencies for Obscura, Xvfb, and stealth Firefox
ARG OBSCURA_VERSION=v0.2.2
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    xvfb \
    libgtk-3-0 \
    libasound2 \
    libdbus-glib-1-2 \
    libx11-xcb1 \
    libxtst6 \
    fonts-liberation \
    procps \
    && curl -sSL -o /tmp/obscura.tar.gz \
       "https://github.com/h4ckf0r0day/obscura/releases/download/${OBSCURA_VERSION}/obscura-x86_64-linux-no-render-stealth.tar.gz" \
    && tar -xzf /tmp/obscura.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/obscura /usr/local/bin/obscura-worker \
    && rm /tmp/obscura.tar.gz \
    && rm -rf /var/lib/apt/lists/*

# Pre-fetch invisible-playwright stealth browser binary
RUN python -m invisible_playwright fetch

# Copy entrypoint and application code
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY src/ ./src/

# Expose the MCP HTTP endpoint port
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "-m", "src.server", "http"]
