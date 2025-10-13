# CyberCore Base Module

## Mô tả
Module nền tảng cho hệ thống quản lý CyberCore ERP - Quản lý quán Internet/Game.

## Tính năng chính

### 1. Menu & Quyền truy cập
- **Menu gốc**: CyberCore ERP
- **Category riêng**: CyberCore (trong Settings → Users & Companies → Groups)
- **3 nhóm quyền**:
  - `Cyber User`: Người dùng cơ bản (chỉ đọc)
  - `Cyber Manager`: Quản lý chi nhánh (đọc, tạo, sửa, xóa)
  - `Cyber Admin`: Quản trị viên (toàn quyền)

### 2. Mở rộng Product Template
Thêm các trường mới vào `product.template`:

**Phân loại:**
- `is_machine`: Đánh dấu sản phẩm là máy chơi
- `is_cyber_service`: Đánh dấu sản phẩm là dịch vụ (đồ ăn, nước uống)
- `service_type`: Loại dịch vụ (food/drink/other)

**Thông tin máy:**
- `ip_address`: Địa chỉ IP của máy
- `location`: Vị trí/khu vực đặt máy
- `status`: Trạng thái (available/playing/maintenance)
- `last_maintenance`: Ngày bảo trì lần cuối

### 3. Dữ liệu khởi tạo

**Danh mục sản phẩm:**
- Máy chơi
- Đồ ăn
- Đồ uống

**Đơn vị đo lường:**
- Giờ (h) - Dành cho thời gian chơi
- Ly (cup) - Dành cho đồ uống
- Gói (pack) - Dành cho gói dịch vụ

### 4. Giao diện

**Menu:**
- CyberCore ERP (menu chính)
  - Sản phẩm Cyber
    - Máy chơi
    - Dịch vụ

**Views:**
- Form view: Hiển thị nhóm "CyberCore Info" với các trường mở rộng
- List view: Hiển thị cột is_machine, is_cyber_service, status
- Search view: Bộ lọc nhanh theo loại sản phẩm và trạng thái

## Cài đặt

### Yêu cầu
- Odoo 18.0
- Python 3.10+
- Module phụ thuộc: base, product, uom

### Các bước cài đặt

1. Copy module vào thư mục addons:
```bash
cp -r cyber_base /path/to/odoo/addons/
```

2. Cập nhật danh sách apps:
- Vào Settings → Apps → Update Apps List

3. Tìm và cài đặt module "CyberCore Base"

### Cài đặt qua Docker

```bash
# Build lại image
docker-compose build

# Cài đặt module
docker-compose run --rm web odoo -i cyber_base -d your_database
```

## Sử dụng

Sau khi cài đặt, bạn sẽ thấy menu **CyberCore ERP** trên thanh menu chính.

### Tạo sản phẩm máy chơi:
1. Vào CyberCore ERP → Máy chơi
2. Tạo mới và tích chọn "Máy chơi (Cyber)"
3. Điền các thông tin: IP, vị trí, trạng thái

### Tạo dịch vụ:
1. Vào CyberCore ERP → Dịch vụ
2. Tạo mới và tích chọn "Dịch vụ Cyber"
3. Chọn loại dịch vụ: Đồ ăn/Đồ uống/Khác

## Module liên quan

Module này là nền tảng cho:
- `cyber_customer`: Quản lý khách hàng
- `cyber_session`: Quản lý phiên chơi
- `cyber_maintenance`: Quản lý bảo trì máy
- `cyber_service`: Quản lý dịch vụ ăn uống
- `cyber_expense`: Quản lý chi phí
- `cyber_report`: Báo cáo tổng hợp

## Tác giả
CyberCore Team

## Giấy phép
LGPL-3
