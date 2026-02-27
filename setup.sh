#!/usr/bin/env bash
# ============================================================
# MedDevice DMS - Setup Script
# ============================================================
set -e

echo "🏥 MedDevice DMS - Setup"
echo "========================"

# 1. Start all services
echo ""
echo "📦 Starting Docker services..."
docker compose up -d

# 1.5. Stop the Bot container to prevent Polling Conflict with local testing
echo "🛑 Stopping Docker Bot to prevent Telegram Conflict Error..."
docker compose stop bot

# 2. Wait for SurrealDB
echo ""
echo "⏳ Waiting for SurrealDB..."
sleep 5

# 3. Apply schema
echo ""
echo "📋 Applying SurrealDB schema..."
docker exec -i $(docker compose ps -q surrealdb) \
  /surreal sql --conn ws://localhost:8000 \
  --user root --pass root \
  --ns meddevice --db dms < db/schema.surql

echo "✅ Schema applied!"

# 4. Create MinIO bucket for Outline
echo ""
echo "🪣 Creating MinIO bucket (outline)..."
docker exec $(docker compose ps -q minio) \
  mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
docker exec $(docker compose ps -q minio) \
  mc mb local/outline 2>/dev/null || true

# 5. Start cloudflared tunnel (optional)
echo ""
echo "🌐 Starting cloudflared tunnel..."
if command -v cloudflared &> /dev/null; then
  cloudflared tunnel --url http://localhost:8080 &
  TUNNEL_PID=$!
  sleep 3
  echo "✅ Tunnel started (PID: $TUNNEL_PID)"
else
  echo "⚠️  cloudflared not found. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/"
  echo "   Or use ngrok: ngrok http 8080"
fi

# 6. Print URLs
echo ""
echo "============================================================"
echo "🏥 MedDevice DMS is running!"
echo "============================================================"
echo ""
echo "  📊 SurrealDB:   http://localhost:8000"
echo "  🌐 Outline Wiki: http://localhost:3000"
echo "  📦 MinIO Console: http://localhost:9001"
echo "  🤖 Bot Webhook:  http://localhost:8080/webhook"
echo ""
echo "  📝 Don't forget to:"
echo "     1. Copy .env.example → .env and fill in secrets"
echo "     2. Set WEBHOOK_URL to your tunnel URL"
echo "     3. Configure Outline auth in .env.outline"
echo ""
