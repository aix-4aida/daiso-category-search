import json

file_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v4_golden_test_cases.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Total cases: {len(data)}")
    
    # Case 47 is index 46
    if len(data) > 46:
        case_47 = data[46]
        print(f"Case 47 (Index 46):")
        print(json.dumps(case_47, indent=2, ensure_ascii=False))
    else:
        print("Data has fewer than 47 cases.")

except Exception as e:
    print(f"Error: {e}")
