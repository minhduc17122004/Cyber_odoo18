# -*- coding: utf-8 -*-
"""
Script kiểm tra module cyber_base
Chạy lệnh: python test_module.py
"""

def check_module_structure():
    """Kiểm tra cấu trúc thư mục"""
    import os
    
    required_files = [
        '__init__.py',
        '__manifest__.py',
        'README.md',
        'INSTALL.md',
        'models/__init__.py',
        'models/cyber_product.py',
        'security/cyber_groups.xml',
        'security/ir.model.access.csv',
        'data/product_category.xml',
        'data/uom_data.xml',
        'views/cyber_menus.xml',
        'views/product_views.xml',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Thiếu các file sau:")
        for f in missing_files:
            print(f"   - {f}")
        return False
    else:
        print("✅ Cấu trúc thư mục hoàn chỉnh")
        return True


def check_manifest():
    """Kiểm tra __manifest__.py"""
    try:
        with open('__manifest__.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Kiểm tra các trường bắt buộc
        required_keys = ['name', 'version', 'depends', 'data']
        for key in required_keys:
            if f'"{key}"' not in content and f"'{key}'" not in content:
                print(f"❌ Thiếu key '{key}' trong __manifest__.py")
                return False
        
        print("✅ __manifest__.py hợp lệ")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi đọc __manifest__.py: {e}")
        return False


def check_python_syntax():
    """Kiểm tra cú pháp Python"""
    import py_compile
    
    python_files = [
        '__init__.py',
        'models/__init__.py',
        'models/cyber_product.py',
    ]
    
    errors = []
    for file_path in python_files:
        try:
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{file_path}: {e}")
    
    if errors:
        print("❌ Lỗi cú pháp Python:")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print("✅ Cú pháp Python hợp lệ")
        return True


def check_xml_syntax():
    """Kiểm tra cú pháp XML"""
    import xml.etree.ElementTree as ET
    
    xml_files = [
        'security/cyber_groups.xml',
        'data/product_category.xml',
        'data/uom_data.xml',
        'views/cyber_menus.xml',
        'views/product_views.xml',
    ]
    
    errors = []
    for file_path in xml_files:
        try:
            ET.parse(file_path)
        except ET.ParseError as e:
            errors.append(f"{file_path}: {e}")
    
    if errors:
        print("❌ Lỗi cú pháp XML:")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print("✅ Cú pháp XML hợp lệ")
        return True


def check_csv_format():
    """Kiểm tra format CSV"""
    import csv
    
    try:
        with open('security/ir.model.access.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if len(rows) == 0:
                print("❌ File ir.model.access.csv rỗng")
                return False
            
            required_cols = ['id', 'name', 'model_id:id', 'group_id:id', 
                           'perm_read', 'perm_write', 'perm_create', 'perm_unlink']
            
            for col in required_cols:
                if col not in reader.fieldnames:
                    print(f"❌ Thiếu cột '{col}' trong ir.model.access.csv")
                    return False
        
        print("✅ Format CSV hợp lệ")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi đọc CSV: {e}")
        return False


def main():
    """Chạy tất cả kiểm tra"""
    print("=" * 60)
    print("🔍 KIỂM TRA MODULE CYBER_BASE")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Kiểm tra cấu trúc thư mục...")
    results.append(check_module_structure())
    print()
    
    print("2. Kiểm tra __manifest__.py...")
    results.append(check_manifest())
    print()
    
    print("3. Kiểm tra cú pháp Python...")
    results.append(check_python_syntax())
    print()
    
    print("4. Kiểm tra cú pháp XML...")
    results.append(check_xml_syntax())
    print()
    
    print("5. Kiểm tra format CSV...")
    results.append(check_csv_format())
    print()
    
    print("=" * 60)
    if all(results):
        print("✅ TẤT CẢ KIỂM TRA THÀNH CÔNG!")
        print("Module sẵn sàng để cài đặt.")
    else:
        print("❌ CÓ LỖI XẢY RA!")
        print("Vui lòng sửa các lỗi trên trước khi cài đặt.")
    print("=" * 60)


if __name__ == '__main__':
    main()
