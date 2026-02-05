import json
from collections import Counter

test_cases_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_golden_test_cases.json'
product_db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
        
    with open(product_db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # 1. Analyze Test Cases
    scenarios = [tc.get('scenario_type', 'Unknown') for tc in test_cases]
    scenario_counts = Counter(scenarios)
    
    # Infer difficulty if not present (Simple heuristic for report)
    # Mapping based on previous context: Synonym/Intent/Visual/Distractor/Typo are generally Harder than Simple
    
    print(f"=== Test Case Analysis (Total: {len(test_cases)}) ===")
    print("Scenario Distribution:")
    for k, v in scenario_counts.most_common():
        print(f"  - {k}: {v} ({v/len(test_cases)*100:.1f}%)")
        
    # Examples per scenario
    print("\nExamples per Scenario:")
    seen_scenarios = set()
    for tc in test_cases:
        sc = tc.get('scenario_type', 'Unknown')
        if sc not in seen_scenarios:
            intent_obj = tc.get('expected_intent', {})
            # Handle different structures of expected_intent
            target = intent_obj.get('target') or intent_obj.get('category') or str(intent_obj.get('keywords', 'Unknown'))
            print(f"  [{sc}] Query: '{tc['query']}' -> Intent: {target}")
            seen_scenarios.add(sc)
            
    # 2. Analyze Product DB
    categories = [p.get('category_major', 'Unknown') for p in products]
    
    print(f"\n=== Product DB Analysis (Total: {len(products)}) ===")
    print("Category Distribution:")
    for k, v in Counter(categories).most_common():
        print(f"  - {k}: {v}")

except Exception as e:
    print(f"Error: {e}")
