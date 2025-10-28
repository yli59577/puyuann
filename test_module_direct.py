# -*- coding: utf-8 -*-
"""
直接測試 JournalModule.get_diary_list 函數
"""
import sys
sys.path.insert(0, 'app')

from app._journal.module import JournalModule

try:
    print("測試 get_diary_list 函數...")
    print("=" * 50)
    
    result = JournalModule.get_diary_list(None, 1, '2025-10-28')
    
    print(f"\n成功! 找到 {len(result)} 筆記錄")
    for i, record in enumerate(result):
        print(f"\n記錄 {i+1}:")
        print(f"  ID: {record.get('id')}")
        print(f"  Type: {record.get('type')}")
        print(f"  Description: {record.get('description')}")
        print(f"  Recorded at: {record.get('recorded_at')}")
    
except Exception as e:
    print(f"\n❌ 錯誤: {str(e)}")
    import traceback
    traceback.print_exc()
