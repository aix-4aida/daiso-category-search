import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_search(query, case_name):
    print(f"\n--- Testing: {case_name} ('{query}') ---")
    url = f"{BASE_URL}/api/search"
    payload = {
        "query": query,
        "input_mode": "text",
        "session_id": "test_session_1"
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload)
        duration = time.time() - start
        
        print(f"Status: {response.status_code} ({duration:.2f}s)")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Result Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('results'):
                print(f"Products Found: {len(data['results'])}")
                for p in data['results'][:2]:
                    print(f" - {p.get('name')} ({p.get('id')})")
            
            if data.get('suggestions'):
                print(f"Suggestions: {data['suggestions']}")
            
            return data
        else:
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    # 1. Normal Search (Expecting Success)
    test_search("건전지", "Normal Item Search")
    
    # 2. Clarification Needed (Vague)
    test_search("거기", "Vague Query (Clarify)")
    
    # 3. Not Supported (Chitchat)
    test_search("안녕 반가워", "Chitchat (Not Supported)")
    
    # 4. No Result (Nonsense)
    test_search("와장창쿵탕", "Nonsense (No Result)")

if __name__ == "__main__":
    main()
