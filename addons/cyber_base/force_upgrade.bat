@echo off
REM Force upgrade module - clear cache and update

echo ========================================
echo  CYBERCORE BASE - FORCE UPGRADE
echo ========================================
echo.
echo This will:
echo - Stop Odoo
echo - Clear Python cache
echo - Force update module
echo - Restart Odoo
echo.

set /p DB_NAME="Enter database name: "
set /p CONFIRM="Are you sure? (Y/N): "

if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Stopping Odoo...
docker-compose stop web

echo.
echo [2/5] Clearing Python cache...
del /s /q __pycache__ >nul 2>&1
del /s /q *.pyc >nul 2>&1

echo.
echo [3/5] Force updating module...
docker-compose run --rm web odoo -u cyber_base -d %DB_NAME% --stop-after-init --log-level=debug

if %errorlevel% neq 0 (
    echo.
    echo ❌ Update failed!
    echo.
    echo Common issues:
    echo 1. Database doesn't exist - use install instead
    echo 2. Module not installed yet - run build_and_install.bat first
    echo 3. Data conflicts - check logs below
    echo.
    docker-compose logs --tail=100 web
    pause
    exit /b 1
)

echo.
echo [4/5] Clearing Odoo cache...
docker-compose run --rm web odoo shell -d %DB_NAME% --stop-after-init -c "env['ir.ui.view'].clear_caches()"

echo.
echo [5/5] Starting Odoo...
docker-compose up -d web

echo.
echo ========================================
echo ✅ UPGRADE COMPLETE!
echo ========================================
echo.
echo Odoo is starting at http://localhost:8069
echo Wait 10-15 seconds for Odoo to fully start
echo.
pause
