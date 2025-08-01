#!/usr/bin/env bash
set -euo pipefail
docker build -t ai-rag-agent:test .
cid=$(docker run -d -p 8000:8000 ai-rag-agent:test)
sleep 2
curl -fsSL http://localhost:8000/health | jq
docker stop "$cid"
