@echo off
@chcp 65001 > nul
:: Always run from the directory containing this script
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo 🏥 MedDevice DMS - Windows Setup
echo ================================

:: 0. Check if Docker is running
echo.
echo 🔍 Checking Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Docker is not running or permissions are insufficient.
    echo Please:
    echo 1. Start Docker Desktop and wait for it to be ready.
    echo 2. Run this script as Administrator.
    pause
    exit /b 1
)

:: 1. Start all services
echo.
echo 📦 Starting Docker services...
set DOCKER_BUILDKIT=0
docker compose up -d

:: 2. Wait for SurrealDB
echo.
echo ⏳ Waiting for SurrealDB (10s)...
timeout /t 10 /nobreak > nul

:: 3. Apply schema
echo.
echo 📋 Applying SurrealDB schema...
:: Get container ID for surrealdb
for /f "tokens=*" %%i in ('docker compose ps -q surrealdb') do set SURREAL_ID=%%i

if "!SURREAL_ID!"=="" (
    echo ❌ Error: SurrealDB container not found.
    pause
    exit /b 1
)

docker exec -i !SURREAL_ID! /surreal sql --user root --pass root --ns meddevice --db dms --endpoint http://localhost:8000 < db/schema.surql

echo ✅ Schema applied!

:: 4. Create MinIO bucket for Outline
echo.
echo 🪣 Creating MinIO bucket (outline)...
for /f "tokens=*" %%i in ('docker compose ps -q minio') do set MINIO_ID=%%i

if not "!MINIO_ID!"=="" (
    docker exec !MINIO_ID! mc alias set local http://localhost:9000 minioadmin minioadmin
    docker exec !MINIO_ID! mc mb local/outline
)

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
