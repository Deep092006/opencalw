#!/bin/sh
set -e

# If an onboarding token is provided via env, run onboarding (non-interactive)
if [ -n "$GITHUB_COPILOT_TOKEN" ]; then
  echo "GITHUB_COPILOT_TOKEN provided — running onboarding..."
  openclaw onboard --non-interactive --accept-risk \
    --auth-choice github-copilot \
    --github-copilot-token "$GITHUB_COPILOT_TOKEN" \
    --skip-channels --skip-health || true
else
  echo "No GITHUB_COPILOT_TOKEN provided — starting in unconfigured mode."
fi

# Ensure gateway binds to LAN so host can reach it
if [ -f /root/.openclaw/openclaw.json ]; then
  sed -i 's/"bind": "loopback"/"bind": "lan"/' /root/.openclaw/openclaw.json || true
  # Use | as delimiter to avoid escaping slashes in model IDs
  sed -i 's|"primary": "github-copilot/claude-opus-4.7"|"primary": "github-copilot/codex-5.2"|' /root/.openclaw/openclaw.json || true
fi

# Optionally allow all Control UI origins (unsafe; use only for testing)
if [ "$CONTROL_UI_ALLOW_ALL_ORIGINS" = "true" ]; then
  openclaw config set gateway.controlUi.allowedOrigins '["*"]' || true
fi

# Optionally allow extra Control UI origins (comma-separated URLs)
if [ -n "$CONTROL_UI_ALLOWED_ORIGINS" ]; then
  ORIGINS_JSON='["http://localhost:18789","http://127.0.0.1:18789"'
  IFS=','
  for origin in $CONTROL_UI_ALLOWED_ORIGINS; do
    ORIGINS_JSON="$ORIGINS_JSON,\"$origin\""
  done
  ORIGINS_JSON="$ORIGINS_JSON]"
  openclaw config set gateway.controlUi.allowedOrigins "$ORIGINS_JSON" || true
  unset IFS
fi

# If running 'openclaw gateway', add --allow-unconfigured flag if no config exists
if [ "$1" = "openclaw" ] && [ "$2" = "gateway" ]; then
  if [ ! -f /root/.openclaw/openclaw.json ]; then
    set -- "$@" "--allow-unconfigured"
  fi
fi

# Exec the CMD (openclaw gateway by default)
exec "$@"
