import os

base = r'c:\kms\daiso-category-search\frontend\src\pages'
files = ['Home.jsx', 'Categories.jsx', 'Map.jsx', 'SearchResults.jsx', 'VoiceSearch.jsx']

print(f"Cleaning types from {base}")

for f in files:
    path = os.path.join(base, f)
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"Deleted {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")
    else:
        print(f"{f} not found")
