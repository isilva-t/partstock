FROM alpine:3.20

# Install curl + bash if needed
RUN apk add --no-cache bash curl

# Install cloudflared
RUN wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -O /usr/local/bin/cloudflared \
 && chmod +x /usr/local/bin/cloudflared

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

