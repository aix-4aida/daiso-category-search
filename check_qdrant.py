import requests
try:
    print("Checking Qdrant...")
    resp = requests.get("http://localhost:6333/collections", timeout=5)
    print(resp.json())
    
    print("Checking Elastic...")
    resp = requests.get("http://localhost:9200/products/_count", timeout=5)
    print(resp.json())
except Exception as e:
    print(e)
