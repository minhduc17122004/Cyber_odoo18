Hướng Dẫn Cài Đặt Odoo (Có Video Hướng Dẫn Phía Dưới) (Đọc Hướng Dẫn Thật Kỹ Trước Khi Cài Đặt)
🔹 Thông Tin Phiên Bản
Odoo 17 & Odoo 18
Đã tích hợp thư viện Odoo Accounting
✅ Ưu & Nhược Điểm
🔥 Ưu Điểm
Dễ triển khai hơn so với cách cài đặt thủ công.
Dễ khắc phục lỗi nếu có sự cố xảy ra.
Dễ gỡ bỏ mà không lo mất dữ liệu như cách cài đặt truyền thống.
Tích hợp sẵn module cần thiết, không cần cài đặt thêm.
Tối ưu tài nguyên, chỉ chạy khi cần, không tốn tài nguyên khi tắt.
Hỗ trợ đa nền tảng (Windows, MacOS, Linux).
⚠️ Nhược Điểm
Cần một ít kiến thức kỹ thuật.
Dung lượng lớn hơn một chút (~50MB, nhưng không đáng kể so với lợi ích mang lại).
📌 Yêu Cầu Thiết Bị (Windows & MacOS)
🔹 Cấu Hình Tối Thiểu
Windows
Hệ điều hành: Windows 10 64-bit trở lên
CPU: Hỗ trợ ảo hóa (VT-x hoặc AMD-V)
RAM: Tối thiểu 4GB (khuyến nghị 8GB trở lên)
Ổ cứng: Tối thiểu 20GB dung lượng trống
Mạng: Kết nối internet ổn định để tải các container Docker
MacOS
Hệ điều hành: macOS 11 (Big Sur) trở lên
CPU: Chip Intel hoặc Apple Silicon (M1, M2,...)
RAM: Tối thiểu 4GB (khuyến nghị 8GB trở lên)
Ổ cứng: Tối thiểu 20GB dung lượng trống
Mạng: Kết nối internet ổn định để tải các container Docker
🔹 Cách Kiểm Tra Cấu Hình
Windows
Kiểm Tra Ảo Hóa CPU
Mở Task Manager (Ctrl + Shift + Esc)
Chuyển sang tab Performance
Chọn mục CPU
Tìm mục Virtualization
Nếu hiển thị Enabled, máy bạn hỗ trợ ảo hóa.
Nếu hiển thị Disabled, cần bật ảo hóa trong BIOS.
MacOS
Kiểm Tra Dung Lượng Ổ Cứng
Nhấn Cmd + Space, gõ "About This Mac" rồi nhấn Enter.
Chọn tab Storage để kiểm tra dung lượng trống.
📌 Chuẩn Bị (Dành Cho Windows & MacOS)
🔹 Windows
Cách 1: Cài Đặt Docker Desktop (Ưu tiên)
Tải và cài đặt Docker Desktop.
Cách 2: Cài Đặt Docker Qua Command Prompt
Mở CMD (Windows + R, nhập cmd, nhấn Enter).

Chạy lệnh sau để cài đặt Docker Desktop:

winget install -e --id Docker.DockerDesktop
Hoàn tất quá trình cài đặt.

🔹 MacOS
Tải Docker Desktop for Mac và chọn đúng phiên bản (Intel Chip là dành cho các máy chạy chip Intel. Apple Silicon là dành cho các máy chạy chip M1,M2,...).
Mở file .dmg, kéo ứng dụng Docker vào thư mục Applications.
Mở Docker, chấp nhận điều khoản sử dụng.
🚀 Cài Đặt Odoo 17 / Odoo 18
Tải về phiên bản mới nhất tại Release.
Giải nén thư mục vừa tải xuống.
Truy cập vào thư mục đã giải nén.
Nhấp chuột phải vào vùng trống trong thư mục, giữ Shift, chọn Open with Terminal hoặc Open with Command Prompt.
MacOS Hướng dẫn sử dụng
Windows
Nhập lệnh sau để khởi chạy Odoo:

docker-compose up -d
Quá trình cài đặt sẽ diễn ra, tốc độ phụ thuộc vào tốc độ mạng và cấu hình máy.

Khi xuất hiện dòng Created (màu xanh), quá trình cài đặt đã hoàn tất.

Truy cập Odoo bằng cách mở trình duyệt và nhập:

http://localhost:8069
Những lần sau chạy, chỉ cần bật Docker Desktop tìm dòng odoo_erp_docker và bấm ⏯️ và truy cập http://localhost:8069 trên trình duyệt Hướng dẫn sử dụng

🔄 Cách Restart Lại Odoo Nếu Gặp Lỗi (Windows & MacOS)
Mở Command Prompt (Windows) hoặc Terminal (MacOS) trong thư mục chứa file docker-compose.yml.

Dừng container:

docker-compose down -v
Khởi động lại container:

docker-compose up -d
Hướng dẫn sử dụng

Đợi một lúc và kiểm tra lại bằng cách truy cập:

http://localhost:8069
Setup mail SMTP trên Odoo (Chỉ sử dụng khi chạy Docker)
alt text

Setup cấu hình giống trong ảnh là được

Sau đó truy cập vào link sau để check mail:

localhost:8025
🎥 Video Hướng Dẫn
Windows: Xem video hướng dẫn

MacOS (Macbook, MacPro, iMac, v.v.): Xem video hướng dẫn

❌ Những Lỗi Phổ Biến (Windows) & Cách Khắc Phục
🔹 Lỗi "Docker Engine Stopped" Khi Chạy Lần Đầu
📌 Giải pháp:

Mở Command Prompt (CMD) dưới quyền Administrator.

Chạy lệnh sau:

wsl --update
wsl --install --no-distribution
Đợi quá trình cập hoàn tất (100%).

Khởi động lại máy tính

Mở lại Docker Desktop, nếu thấy "Docker Engine starting..." thì chờ một chút để nó khởi động.

💡 Chúc bạn cài đặt thành công! 🚀
