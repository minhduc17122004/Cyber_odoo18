@echo off
REM Script nhanh để update module cyber_base

echo ========================================
echo  CYBERCORE BASE - QUICK UPDATE
echo ========================================
echo.

set /p DB_NAME="Nhập tên database: "

echo.
echo [*] Đang cập nhật module...
docker-compose run --rm web odoo -u cyber_base -d %DB_NAME% --stop-after-init

echo.
echo [*] Khởi động lại container...
docker-compose restart web

echo.
echo ✅ Hoàn thành! Module đã được cập nhật.
echo.
pause
