@echo off
REM Script nhanh để build và cài đặt cyber_base module

echo ========================================
echo  CYBERCORE BASE - BUILD ^& INSTALL
echo ========================================
echo.

REM Kiểm tra module
echo [1/4] Kiểm tra module...
python test_module.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Module có lỗi! Vui lòng kiểm tra lại.
    pause
    exit /b 1
)

echo.
echo [2/4] Build Docker image...
docker-compose build
if %errorlevel% neq 0 (
    echo.
    echo ❌ Build thất bại!
    pause
    exit /b 1
)

echo.
echo [3/4] Khởi động container...
docker-compose up -d
if %errorlevel% neq 0 (
    echo.
    echo ❌ Không thể khởi động container!
    pause
    exit /b 1
)

echo.
echo [4/4] Cài đặt/Nâng cấp module...
set /p DB_NAME="Input your name database: "
docker-compose run --rm web odoo -u cyber_base -d %DB_NAME% --stop-after-init
if %errorlevel% neq 0 (
    echo.
    echo ❌ Cài đặt thất bại!
    pause
    exit /b 1
)

echo.
echo [*] Khởi động lại container...
docker-compose restart web

echo.
echo ========================================
echo ✅ HOÀN THÀNH!
echo ========================================
echo.
echo Module cyber_base đã được cài đặt/nâng cấp thành công.
echo Truy cập: http://localhost:8069
echo.
pause
