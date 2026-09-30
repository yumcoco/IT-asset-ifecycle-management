import sys
import os
import sqlite3

# 正确计算数据库路径
# 根据错误消息，脚本运行在 /Users/lisa/it_management_mock/check_db.py
# 所以项目根目录是 /Users/lisa/it_management_mock
project_root = '/Users/lisa/it_management_mock'
db_path = os.path.join(project_root, 'data', 'db', 'supply_chain.sqlite')

print(f"Checking for database at: {db_path}")

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"Database file not found at: {db_path}")

    # 检查data目录是否存在
    data_dir = os.path.join(project_root, 'data')
    if os.path.exists(data_dir):
        print(f"Data directory exists: {data_dir}")
        # 检查db目录是否存在
        db_dir = os.path.join(data_dir, 'db')
        if os.path.exists(db_dir):
            print(f"DB directory exists: {db_dir}")
            # 列出db目录中的所有文件
            print(f"Files in DB directory: {os.listdir(db_dir)}")
        else:
            print(f"DB directory doesn't exist: {db_dir}")
    else:
        print(f"Data directory doesn't exist: {data_dir}")

    # 尝试搜索项目中的所有sqlite文件
    print("\nSearching for SQLite files in the project...")
    found_files = []

    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.sqlite') or file.endswith('.db'):
                found_path = os.path.join(root, file)
                found_files.append(found_path)
                print(f"Found database file: {found_path}")

    if not found_files:
        print("No SQLite database files found in the project.")

    sys.exit(1)

# 连接到数据库
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 列出所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f" - {table[0]}")

    # 检查inventory表结构
    try:
        cursor.execute("PRAGMA table_info(inventory);")
        columns = cursor.fetchall()
        print("\nInventory table columns:")
        for col in columns:
            print(f" - {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error checking inventory table: {e}")

    # 检查inventory表中的记录数
    try:
        cursor.execute("SELECT COUNT(*) FROM inventory;")
        count = cursor.fetchone()[0]
        print(f"\nNumber of records in inventory table: {count}")

        # 显示几条示例数据
        if count > 0:
            cursor.execute("SELECT id, device_name, device_type, quantity, status FROM inventory LIMIT 5;")
            records = cursor.fetchall()
            print("\nSample inventory records:")
            for rec in records:
                print(
                    f" - ID: {rec[0]}, Name: {rec[1]}, Type: {rec[2]}, Quantity: {rec[3]}, Status: {rec[4] if len(rec) > 4 else 'None'}")
    except Exception as e:
        print(f"Error checking inventory records: {e}")

    conn.close()
except Exception as e:
    print(f"Error connecting to database: {e}")