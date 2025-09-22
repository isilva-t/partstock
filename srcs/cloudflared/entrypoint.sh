#!/bin/sh
# Run quick tunnel, log output, and save URL to file

cloudflared tunnel --url http://temp-server:80 2>&1 | tee /tmp/cloudflare.log | \
awk 'match($0, /https:\/\/[a-zA-Z0-9.-]+\.trycloudflare\.com/) { print substr($0, RSTART, RLENGTH) > "/shared/link.txt" }'

