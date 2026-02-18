#!/bin/bash
# Robust start script for nanobot on Render
# Usage: ./render-start.sh

# If GROQ_API_KEY is set and NANOBOT_CONFIG is not, create a basic config
if [ -n "$GROQ_API_KEY" ] && [ -z "$NANOBOT_CONFIG" ]; then
  export NANOBOT_CONFIG="{\"providers\": {\"groq\": {\"api_key\": \"$GROQ_API_KEY\"}}}"
fi

# Run the gateway
# The gateway automatically respects the $PORT environment variable
exec python3 -m nanobot gateway
