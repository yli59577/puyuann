import sqlite3

def add_columns():
    db_path = 'Puyuan.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ('fb_id', 'VARCHAR'),
        ('google_id', 'VARCHAR'),
        ('apple_id', 'VARCHAR')
    ]
    
    table_name = 'user_profiles'
    
    print(f"Checking table {table_name}...")
    
    # Get existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [info[1] for info in cursor.fetchall()]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            print(f"Adding column {col_name} ({col_type})...")
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                print(f"Successfully added {col_name}")
            except Exception as e:
                print(f"Failed to add {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    add_columns()
