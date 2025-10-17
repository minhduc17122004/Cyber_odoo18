# 🔄 UPGRADE GUIDE - CyberCore Base

## Khi nào cần upgrade?

- Sau khi sửa code trong models/
- Sau khi sửa views/
- Sau khi sửa security rules
- Sau khi thay đổi __manifest__.py

## Các bước upgrade

### ✅ Cách 1: Quick Update (Khuyến nghị)

```cmd
quick_update.bat
```

Nhập tên database và chờ.

### 🔥 Cách 2: Force Upgrade (Khi gặp lỗi)

```cmd
force_upgrade.bat
```

Sử dụng khi:
- quick_update.bat thất bại
- Views không cập nhật
- Có lỗi cache

### 💪 Cách 3: Manual (Nâng cao)

```cmd
# Stop container
docker-compose stop web

# Update module
docker-compose run --rm web odoo -u cyber_base -d your_db --stop-after-init

# Start container
docker-compose up -d web
```

## ⚠️ Lưu ý quan trọng

### About noupdate="1"

**Files có noupdate="1"** (data/):
- `product_category.xml`
- `uom_data.xml`

➡️ Dữ liệu chỉ tạo lần đầu, **KHÔNG** update khi upgrade
➡️ Nếu user đã sửa categories/UoM, giữ nguyên thay đổi của user

**Files KHÔNG có noupdate** (security/):
- `cyber_groups.xml`

➡️ Luôn update khi upgrade module
➡️ Tên groups sẽ được cập nhật theo code mới

### Khi đổi tên field hoặc model

Nếu bạn:
- Đổi tên field (VD: `is_machine` → `is_gaming_machine`)
- Xóa field
- Đổi type của field

➡️ **CẦN** migration script hoặc uninstall/reinstall module

### Khi thêm field mới

Chỉ cần upgrade bình thường:
```cmd
quick_update.bat
```

## 🐛 Troubleshooting

### Module không update

**Triệu chứng:** Thay đổi code nhưng không thấy trên UI

**Giải pháp:**
```cmd
force_upgrade.bat
```

### Lỗi "Field does not exist"

**Nguyên nhân:** Đã xóa/đổi tên field nhưng view vẫn reference field cũ

**Giải pháp:**
1. Kiểm tra tất cả XML views
2. Tìm field cũ: `grep -r "old_field_name" views/`
3. Sửa hoặc xóa references

### Lỗi "External ID not found"

**Nguyên nhân:** Reference đến record không tồn tại

**Giải pháp:**
1. Kiểm tra ref="" trong XML
2. Đảm bảo record được tạo trước khi reference
3. Kiểm tra thứ tự files trong __manifest__.py

### Views không cập nhật

**Giải pháp:**
```cmd
# Clear cache
docker-compose exec web odoo shell -d your_db
>>> env['ir.ui.view'].clear_caches()
>>> exit()

# Restart
docker-compose restart web
```

### Database không tồn tại

**Triệu chứng:** `database "xyz" does not exist`

**Giải pháp:**
1. Kiểm tra database name: `docker-compose exec db psql -U odoo -l`
2. Hoặc tạo database mới qua UI: http://localhost:8069/web/database/manager

## 📝 Best Practices

1. **Luôn test trước:** Test trong dev database trước khi upgrade production

2. **Backup trước khi upgrade:**
   ```cmd
   docker-compose exec db pg_dump -U odoo your_db > backup.sql
   ```

3. **Kiểm tra logs:**
   ```cmd
   docker-compose logs -f web
   ```

4. **Upgrade từng bước:**
   - Sửa 1 file
   - Upgrade
   - Test
   - Lặp lại

5. **Đọc error messages:** Odoo error rất chi tiết, đọc kỹ để biết vấn đề

## 🎯 Quick Commands

```cmd
# Update module
docker-compose run --rm web odoo -u cyber_base -d db_name --stop-after-init

# Install module (lần đầu)
docker-compose run --rm web odoo -i cyber_base -d db_name --stop-after-init

# Uninstall module
docker-compose run --rm web odoo shell -d db_name
>>> env['ir.module.module'].search([('name','=','cyber_base')]).button_immediate_uninstall()

# View logs
docker-compose logs -f web | grep cyber_base

# Clear cache
docker-compose restart web
```

## ✅ Checklist sau upgrade

- [ ] Module hiển thị đúng version trong Apps
- [ ] Menu "CyberCore" hiển thị
- [ ] Views mới xuất hiện
- [ ] Fields mới có trong form
- [ ] Không có error trong logs
- [ ] Test tạo/sửa/xóa records

---

**Note:** Nếu gặp vấn đề không giải quyết được, xem logs chi tiết:
```cmd
docker-compose logs --tail=200 web > error.log
```
