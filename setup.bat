@echo off
setlocal enabledelayedexpansion

echo 🏥 MedDevice DMS - Windows Setup
echo ================================

:: 1. Start all services
echo.
echo 📦 Starting Docker services...
docker-compose up -d

:: 2. Wait for SurrealDB
echo.
echo ⏳ Waiting for SurrealDB (10s)...
timeout /t 10 /nobreak > nul

:: 3. Apply schema
echo.
echo 📋 Applying SurrealDB schema...
:: Get container ID for surrealdb
for /f "tokens=*" %%i in ('docker-compose ps -q surrealdb') do set SURREAL_ID=%%i

if "!SURREAL_ID!"=="" (
    echo ❌ Error: SurrealDB container not found.
    exit /b 1
)

docker exec -i !SURREAL_ID! /surreal sql --conn ws://localhost:8000 --user root --pass root --ns meddevice --db dms < db/schema.surql

echo ✅ Schema applied!

:: 4. Create MinIO bucket for Outline
echo.
echo 🪣 Creating MinIO bucket (outline)...
for /f "tokens=*" %%i in ('docker-compose ps -q minio') do set MINIO_ID=%%i

docker exec !MINIO_ID! mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec !MINIO_ID! mc mb local/outline

:: 5. Print URLs
echo.
echo ============================================================
echo 🏥 MedDevice DMS is running!
echo ============================================================
echo.
echo   📊 SurrealDB:   http://localhost:8000
echo   🌐 Outline Wiki: http://localhost:3000
echo   📦 MinIO Console: http://localhost:9001
echo   🤖 Bot Webhook:  http://localhost:8080/webhook
echo.
echo   📝 Don't forget to:
echo      1. Update .env with your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY
echo      2. Update TELEGRAM_ALLOWED_USERS in .env
echo      3. Start a tunnel (ngrok or cloudflared) and update WEBHOOK_URL
echo.
pause
