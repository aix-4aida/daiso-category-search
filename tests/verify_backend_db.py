import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def verify_health():
    print(f"Endpoint: {BASE_URL}/health")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print("✅ Backend Health: OK")
            print(resp.json())
            return True
        else:
            print(f"❌ Backend Health Failed: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend Connection Failed (Is server running?)")
        return False

def verify_search(query="냄비"):
    print(f"\nEndpoint: {BASE_URL}/search/text (Query: {query})")
    try:
        resp = requests.post(f"{BASE_URL}/search/text", json={"query": query})
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "success":
                print("✅ Search Success")
                result = data["result"]
                print(f"   Product: {result['product']}")
                print(f"   ID: {result['id']}")
                print(f"   Location: {result['location']}")
                print(f"   Candidates: {len(data['candidates'])}")
                return True
            else:
                print(f"❌ Search Failed Logic: {data}")
                return False
        else:
            print(f"❌ Search Request Failed: {resp.status_code}")
            print(resp.text)
            return False
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Verifying Backend DB Connection...")
    
    # Wait for server to start if just launched
    for i in range(5):
        if verify_health():
            break
        print(f"Waiting for server... ({i+1}/5)")
        time.sleep(2)
    else:
        print("❌ Server failed to start or is unreachable.")
        sys.exit(1)

    if verify_search():
        print("\n✨ Verification Complete: Frontend-Backend-DB Integration seems valid.")
        sys.exit(0)
    else:
        print("\n❌ Verification Failed.")
        sys.exit(1)
