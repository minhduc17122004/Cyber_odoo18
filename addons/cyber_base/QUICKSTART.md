# 🚀 QUICK START - CYBER_BASE MODULE

## ⚡ Cài đặt nhanh (3 phút)

### 1. Kiểm tra module
```cmd
python test_module.py
```
✅ Phải thấy "TẤT CẢ KIỂM TRA THÀNH CÔNG!"

### 2. Build & Install
```cmd
build_and_install.bat
```
📝 Nhập tên database khi được hỏi

### 3. Truy cập
```
URL: http://localhost:8069
Menu: CyberCore ERP
```

## 🎯 Test nhanh

### Tạo máy chơi:
1. CyberCore ERP → Máy chơi → Tạo mới
2. Name: "Máy 01"
3. Tích: ☑ Máy chơi (Cyber)
4. IP: 192.168.1.101
5. Location: "Khu A"
6. Status: Sẵn sàng
7. Save

### Tạo dịch vụ:
1. CyberCore ERP → Dịch vụ → Tạo mới
2. Name: "Pepsi"
3. Tích: ☑ Dịch vụ Cyber
4. Service Type: Đồ uống
5. Price: 10000
6. Save

## ✅ Kiểm tra thành công

- [ ] Menu "CyberCore ERP" hiển thị
- [ ] Có thể tạo máy chơi
- [ ] Có thể tạo dịch vụ
- [ ] Filters hoạt động
- [ ] Groups được tạo (Settings → Users → Groups)

## 🔄 Update sau khi sửa code

```cmd
quick_update.bat
```

## 📚 Tài liệu đầy đủ

- **SUMMARY.md** - Tổng quan module
- **README.md** - Chi tiết tính năng
- **INSTALL.md** - Hướng dẫn cài đặt
- **CHECKLIST.md** - Danh sách kiểm tra

## ⚠️ Lưu ý

- Cần Docker đang chạy
- Database phải đã tồn tại
- Port 8069 phải trống

## 🆘 Gặp lỗi?

```cmd
# Xem log
docker-compose logs -f web

# Restart container
docker-compose restart web

# Rebuild từ đầu
docker-compose down
docker-compose build
docker-compose up -d
```

---

**Thời gian**: ~3 phút  
**Độ khó**: ⭐⭐☆☆☆ (Dễ)  
**Status**: ✅ Sẵn sàng
