# Hướng Dẫn Cài Đặt Odoo (Docker)

> ⚠️ Đọc kỹ hướng dẫn trước khi cài đặt. Video hướng dẫn có phía dưới.

---

## Mục Lục
1. [Thông Tin Phiên Bản](#thông-tin-phiên-bản)
2. [Ưu & Nhược Điểm](#ưu--nhược-điểm)
3. [Yêu Cầu Thiết Bị](#yêu-cầu-thiết-bị)
4. [Kiểm Tra Cấu Hình](#kiểm-tra-cấu-hình)
5. [Chuẩn Bị Cài Đặt](#chuẩn-bị-cài-đặt)
6. [Cài Đặt Odoo](#cài-đặt-odoo)
7. [Restart Odoo Khi Gặp Lỗi](#restart-odoo-khi-gặp-lỗi)
8. [Cấu Hình Mail SMTP](#cấu-hình-mail-smtp)
9. [Video Hướng Dẫn](#video-hướng-dẫn)
10. [Lỗi Phổ Biến & Khắc Phục](#lỗi-phổ-biến--khắc-phục)

---

## Thông Tin Phiên Bản
- Odoo 17 & Odoo 18  
- Đã tích hợp **Odoo Accounting**

---

## Ưu & Nhược Điểm

### Ưu Điểm
- Dễ triển khai hơn cài đặt thủ công  
- Dễ khắc phục lỗi, dễ gỡ bỏ mà không mất dữ liệu  
- Tích hợp sẵn các module cần thiết  
- Tối ưu tài nguyên: chỉ chạy khi cần  
- Hỗ trợ đa nền tảng: Windows, MacOS, Linux  

### Nhược Điểm
- Cần một ít kiến thức kỹ thuật  
- Dung lượng lớn hơn một chút (~50MB)  

---

## Yêu Cầu Thiết Bị

### Windows
- OS: Windows 10 64-bit trở lên  
- CPU: hỗ trợ ảo hóa (VT-x hoặc AMD-V)  
- RAM: 4GB (khuyến nghị 8GB)  
- Ổ cứng: ≥20GB trống  
- Mạng: kết nối internet ổn định  

### MacOS
- OS: macOS 11 (Big Sur) trở lên  
- CPU: Intel hoặc Apple Silicon (M1, M2, …)  
- RAM: 4GB (khuyến nghị 8GB)  
- Ổ cứng: ≥20GB trống  
- Mạng: kết nối internet ổn định  

---

## Kiểm Tra Cấu Hình

### Windows
1. Ctrl + Shift + Esc → Tab **Performance** → **CPU**  
2. Kiểm tra **Virtualization**:  
   - Enabled → hỗ trợ ảo hóa  
   - Disabled → bật trong BIOS  

### MacOS
1. Cmd + Space → gõ "About This Mac" → Enter  
2. Tab **Storage** → kiểm tra dung lượng trống  

---

## Chuẩn Bị Cài Đặt

### Windows
- **Cách 1 (Ưu tiên):** Cài Docker Desktop  
- **Cách 2:** Cài Docker qua CMD:
```bash
winget install -e --id Docker.DockerDesktop
MacOS
Tải Docker Desktop for Mac → chọn đúng phiên bản (Intel / Apple Silicon)

Mở .dmg → kéo Docker vào Applications

Mở Docker → chấp nhận điều khoản

Cài Đặt Odoo
Tải phiên bản mới nhất tại Release

Giải nén thư mục

Mở Terminal/Command Prompt tại thư mục giải nén

Windows / MacOS
bash
Sao chép mã
docker-compose up -d
Sau khi thấy dòng Created (màu xanh) → truy cập Odoo:

arduino
Sao chép mã
http://localhost:8069
Lần sau: bật Docker Desktop → tìm odoo_erp_docker → bấm ⏯️ → truy cập http://localhost:8069

Restart Odoo Khi Gặp Lỗi
bash
Sao chép mã
docker-compose down -v
docker-compose up -d
Chờ vài giây → truy cập lại http://localhost:8069

Cấu Hình Mail SMTP (Docker)
Setup giống hình hướng dẫn

Kiểm tra mail tại:

arduino
Sao chép mã
http://localhost:8025
Video Hướng Dẫn
Windows: Xem video

MacOS: Xem video

Lỗi Phổ Biến & Khắc Phục (Windows)
Lỗi "Docker Engine Stopped"
Giải pháp:

bash
Sao chép mã
wsl --update
wsl --install --no-distribution
Đợi 100% → khởi động lại máy → mở Docker Desktop

💡 Chúc bạn cài đặt thành công! 🚀

css
Sao chép mã

---

Nếu bạn muốn, mình có thể làm thêm **phiên bản README có hình minh họa, bảng so sánh cấu hình, và hướng dẫn lệnh Docker trực quan** để người dùng dễ theo dõi hơn. Bạn có muốn mình làm luôn không?
Dưới đây là phiên bản README đã được viết lại, gọn gàng, chuẩn Markdown, có mục lục và hướng dẫn chi tiết cho Odoo Docker:

markdown
Sao chép mã
# Hướng Dẫn Cài Đặt Odoo (Docker)

> ⚠️ Đọc kỹ hướng dẫn trước khi cài đặt. Video hướng dẫn có phía dưới.

---

## Mục Lục
1. [Thông Tin Phiên Bản](#thông-tin-phiên-bản)
2. [Ưu & Nhược Điểm](#ưu--nhược-điểm)
3. [Yêu Cầu Thiết Bị](#yêu-cầu-thiết-bị)
4. [Kiểm Tra Cấu Hình](#kiểm-tra-cấu-hình)
5. [Chuẩn Bị Cài Đặt](#chuẩn-bị-cài-đặt)
6. [Cài Đặt Odoo](#cài-đặt-odoo)
7. [Restart Odoo Khi Gặp Lỗi](#restart-odoo-khi-gặp-lỗi)
8. [Cấu Hình Mail SMTP](#cấu-hình-mail-smtp)
9. [Video Hướng Dẫn](#video-hướng-dẫn)
10. [Lỗi Phổ Biến & Khắc Phục](#lỗi-phổ-biến--khắc-phục)

---

## Thông Tin Phiên Bản
- Odoo 17 & Odoo 18  
- Đã tích hợp **Odoo Accounting**

---

## Ưu & Nhược Điểm

### Ưu Điểm
- Dễ triển khai hơn cài đặt thủ công  
- Dễ khắc phục lỗi và gỡ bỏ mà không mất dữ liệu  
- Tích hợp sẵn các module cần thiết  
- Tối ưu tài nguyên: chỉ chạy khi cần  
- Hỗ trợ đa nền tảng: Windows, MacOS, Linux  

### Nhược Điểm
- Cần một ít kiến thức kỹ thuật  
- Dung lượng lớn hơn một chút (~50MB)  

---

## Yêu Cầu Thiết Bị

### Windows
- OS: Windows 10 64-bit trở lên  
- CPU: hỗ trợ ảo hóa (VT-x hoặc AMD-V)  
- RAM: 4GB (khuyến nghị 8GB)  
- Ổ cứng: ≥20GB trống  
- Mạng: kết nối internet ổn định  

### MacOS
- OS: macOS 11 (Big Sur) trở lên  
- CPU: Intel hoặc Apple Silicon (M1, M2, …)  
- RAM: 4GB (khuyến nghị 8GB)  
- Ổ cứng: ≥20GB trống  
- Mạng: kết nối internet ổn định  

---

## Kiểm Tra Cấu Hình

### Windows
1. Ctrl + Shift + Esc → Tab **Performance** → **CPU**  
2. Kiểm tra **Virtualization**:  
   - Enabled → hỗ trợ ảo hóa  
   - Disabled → bật trong BIOS  

### MacOS
1. Cmd + Space → gõ "About This Mac" → Enter  
2. Tab **Storage** → kiểm tra dung lượng trống  

---

## Chuẩn Bị Cài Đặt

### Windows
- **Cách 1 (Ưu tiên):** Cài Docker Desktop  
- **Cách 2:** Cài Docker qua CMD:
```bash
winget install -e --id Docker.DockerDesktop
MacOS
Tải Docker Desktop for Mac → chọn đúng phiên bản (Intel / Apple Silicon)

Mở .dmg → kéo Docker vào Applications

Mở Docker → chấp nhận điều khoản

Cài Đặt Odoo
Tải phiên bản mới nhất tại Release

Giải nén thư mục

Mở Terminal/Command Prompt tại thư mục giải nén

Windows / MacOS
bash
Sao chép mã
docker-compose up -d
Sau khi thấy dòng Created (màu xanh) → truy cập Odoo:

arduino
Sao chép mã
http://localhost:8069
Lần sau: bật Docker Desktop → tìm odoo_erp_docker → bấm ⏯️ → truy cập http://localhost:8069

Restart Odoo Khi Gặp Lỗi
bash
Sao chép mã
docker-compose down -v
docker-compose up -d
Chờ vài giây → truy cập lại http://localhost:8069

Cấu Hình Mail SMTP (Docker)
Setup giống hình hướng dẫn

Kiểm tra mail tại:

arduino
Sao chép mã
http://localhost:8025
Video Hướng Dẫn
Windows: Xem video

MacOS: Xem video

Lỗi Phổ Biến & Khắc Phục (Windows)
Lỗi "Docker Engine Stopped"
Giải pháp:

bash
Sao chép mã
wsl --update
wsl --install --no-distribution
Đợi 100% → khởi động lại máy → mở Docker Desktop

💡 Chúc bạn cài đặt thành công! 🚀
