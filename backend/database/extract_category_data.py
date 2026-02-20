import json

def extract_categories():
    try:
        with open('backend/database/debug_html/component_tree_search.json', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find CtgrLayer
        ctgr_layer = next((item for item in data if item.get('name') == 'CtgrLayer'), None)
        
        if not ctgr_layer:
            print("CtgrLayer not found")
            return

        layer_data = ctgr_layer.get('data', {})
        
        print("Keys:", layer_data.keys())
        
        category_tree = layer_data.get('categoryTree')
        
        if category_tree:
            print(f"Category Tree Length: {len(category_tree)}")
            for i, d1 in enumerate(category_tree[:5]):
                if isinstance(d1, list):
                    print(f"[{i}] Item is a LIST: {d1[:2]}...")
                    continue
                if not isinstance(d1, dict):
                    print(f"[{i}] Item is {type(d1)}")
                    continue
                    
                d1_name = d1.get('title') or d1.get('name') or "Unknown"
                sub_arr = d1.get('subCateArr', [])
                if isinstance(sub_arr, list):
                     print(f"[{i}] {d1_name} (Has {len(sub_arr)} subcategories)")
                     for j, d2 in enumerate(sub_arr[:3]):
                        if isinstance(d2, dict):
                            d2_name = d2.get('subTitle') or d2.get('name') or d2.get('title') or "Unknown"
                            d2_link = d2.get('link') or d2.get('subMenuLink')
                            print(f"  - {d2_name}: {d2_link}")
                        else:
                            print(f"  - Item {j} is {type(d2)}: {d2}")
                else:
                     print(f"[{i}] {d1_name} subCateArr is {type(sub_arr)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_categories()
