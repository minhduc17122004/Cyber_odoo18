# Hướng dẫn Build & Deploy CyberCore Base Module

## 📋 Kiểm tra trước khi build

### 1. Cấu trúc thư mục
```
cyber_base/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   ├── product_category.xml
│   └── uom_data.xml
├── models/
│   ├── __init__.py
│   └── cyber_product.py
├── security/
│   ├── cyber_groups.xml
│   └── ir.model.access.csv
├── static/
│   └── description/
└── views/
    ├── cyber_menus.xml
    └── product_views.xml
```

### 2. Kiểm tra dependencies
Module phụ thuộc vào:
- `base`
- `product`
- `uom`

## 🐳 Build với Docker

### Bước 1: Cập nhật docker-compose.yaml

Đảm bảo file `docker-compose.yaml` đã mount thư mục addons:

```yaml
services:
  web:
    image: odoo:18.0
    volumes:
      - ./addons:/mnt/extra-addons
    environment:
      - ADDONS_PATH=/mnt/extra-addons
```

### Bước 2: Build lại image

```cmd
docker-compose build
```

### Bước 3: Khởi động container

```cmd
docker-compose up -d
```

### Bước 4: Cài đặt module

**Cách 1: Qua giao diện Web**
1. Truy cập: http://localhost:8069
2. Đăng nhập với tài khoản admin
3. Vào Settings → Apps
4. Nhấn "Update Apps List"
5. Tìm "CyberCore Base"
6. Nhấn "Install"

**Cách 2: Qua command line**

```cmd
docker-compose run --rm web odoo -i cyber_base -d your_database_name
```

### Bước 5: Nâng cấp module (nếu đã cài)

```cmd
docker-compose run --rm web odoo -u cyber_base -d your_database_name
```

## 🔧 Cài đặt trực tiếp (không dùng Docker)

### Bước 1: Copy module

```cmd
xcopy /E /I cyber_base C:\path\to\odoo\addons\cyber_base
```

### Bước 2: Khởi động Odoo server

```cmd
python odoo-bin -c odoo.conf --addons-path=addons,custom_addons
```

### Bước 3: Cài đặt qua giao diện

Tương tự như phần Docker - Cách 1

## ✅ Kiểm tra sau khi cài đặt

### 1. Kiểm tra Menu
- Menu "CyberCore ERP" xuất hiện trên thanh menu chính
- Submenu "Sản phẩm Cyber", "Máy chơi", "Dịch vụ"

### 2. Kiểm tra Groups
Vào Settings → Users & Companies → Groups:
- Cyber User
- Cyber Manager
- Cyber Administrator

### 3. Kiểm tra Product
Vào CyberCore ERP → Sản phẩm Cyber → Tạo mới:
- Checkbox "Máy chơi (Cyber)" hiển thị
- Checkbox "Dịch vụ Cyber" hiển thị
- Khi tích "Máy chơi": hiện trường IP, Location, Status, Last Maintenance
- Khi tích "Dịch vụ Cyber": hiện trường Service Type

### 4. Kiểm tra Categories
Vào Product → Configuration → Product Categories:
- Máy chơi
- Đồ ăn
- Đồ uống

### 5. Kiểm tra UoM
Vào Product → Configuration → Units of Measure:
- Giờ (h)
- Ly (cup)
- Gói (pack)

## 🐛 Troubleshooting

### Lỗi: Module không xuất hiện trong Apps List

**Giải pháp:**
1. Kiểm tra file `__manifest__.py` có đúng cú pháp không
2. Clear browser cache
3. Chạy lại "Update Apps List"
4. Kiểm tra log: `docker-compose logs web`

### Lỗi: External ID not found (module_category_sales_management)

**Mô tả:** Lỗi `ValueError: External ID not found in the system: base.module_category_sales_management`

**Nguyên nhân:** Odoo 18 đã thay đổi/loại bỏ một số module categories cũ.

**Giải pháp:** ✅ Đã sửa! Module bây giờ tạo category riêng `module_category_cybercore` thay vì dùng category cũ của Odoo.

### Lỗi: Import error

**Giải pháp:**
```cmd
# Kiểm tra Python syntax
python -m py_compile cyber_base/models/cyber_product.py

# Restart Odoo
docker-compose restart web
```

### Lỗi: XML parsing error

**Giải pháp:**
- Kiểm tra XML syntax
- Đảm bảo tất cả tag được đóng đúng
- Kiểm tra xpath expression

### Lỗi: Access rights

**Giải pháp:**
```cmd
# Cập nhật lại quyền
docker-compose run --rm web odoo -u cyber_base -d your_database_name --stop-after-init
```

## 🔄 Update Module

Khi có thay đổi code:

```cmd
# Stop container
docker-compose down

# Rebuild (nếu cần)
docker-compose build

# Start và update module
docker-compose up -d
docker-compose exec web odoo -u cyber_base -d your_database_name --stop-after-init
docker-compose restart web
```

## 📝 Ghi chú

- Luôn backup database trước khi cài/nâng cấp module
- Test trên môi trường dev trước khi deploy production
- Kiểm tra log nếu có lỗi: `docker-compose logs -f web`

## 🎯 Tiếp theo

Sau khi module `cyber_base` hoạt động ổn định, bạn có thể phát triển các module mở rộng:

1. **cyber_customer**: Quản lý khách hàng
   ```python
   depends = ['cyber_base', 'contacts']
   ```

2. **cyber_session**: Quản lý phiên chơi
   ```python
   depends = ['cyber_base', 'cyber_customer']
   ```

3. **cyber_maintenance**: Quản lý bảo trì
   ```python
   depends = ['cyber_base']
   ```

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
- Log file: `docker-compose logs web`
- Odoo log level: Set to `debug` trong config
- Community forum: https://www.odoo.com/forum
