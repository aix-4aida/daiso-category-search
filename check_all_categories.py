import sys
import os

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

try:
    from backend.database.database import get_all_category_majors
    
    print("Fetching categories...")
    cats = get_all_category_majors()
    
    print(f"Found {len(cats)} categories")
    
    with open('all_categories.txt', 'w', encoding='utf-8') as f:
        for c in cats:
            print(c)
            f.write(str(c) + '\n')
            
    print("Saved to all_categories.txt")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
