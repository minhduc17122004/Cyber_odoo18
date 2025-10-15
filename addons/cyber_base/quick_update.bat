@echo off
REM Quick script to update cyber_base module

echo ========================================
echo  CYBERCORE BASE - QUICK UPDATE
echo ========================================
echo.

set /p DB_NAME="Enter database name: "

echo.
echo [1/3] Stopping container...
docker-compose stop web

echo.
echo [2/3] Updating module...
docker-compose run --rm web odoo -u cyber_base -d %DB_NAME% --stop-after-init --log-level=info

if %errorlevel% neq 0 (
    echo.
    echo ❌ Update failed! Check the error above.
    echo Trying to view logs...
    docker-compose logs --tail=50 web
    pause
    exit /b 1
)

echo.
echo [3/3] Starting container...
docker-compose up -d web

echo.
echo ✅ Complete! Module has been updated.
echo Odoo is starting at http://localhost:8069
echo.
pause
