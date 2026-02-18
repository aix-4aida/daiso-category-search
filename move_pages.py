import os
import shutil

src = r'c:\kms\daiso-category-search\frontend\src\pages'
dst = r'c:\kms\daiso-category-search\frontend\src\pages_backup'

try:
    if os.path.exists(src):
        if os.path.exists(dst):
            print(f"Removing existing backup: {dst}")
            shutil.rmtree(dst)
        
        os.rename(src, dst)
        print(f"Successfully moved {src} to {dst}")
    else:
        print(f"Source directory not found: {src}")
        
except Exception as e:
    print(f"Error moving directory: {e}")
