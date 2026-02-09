# Qdrant와 Elasticsearch 사용 가이드 (Windows)

이 가이드는 Windows 환경에서 Qdrant(벡터 데이터베이스)와 Elasticsearch(검색 엔진)를 설치하고 사용하는 방법을 설명합니다. 가장 권장되는 방법인 **Docker**를 사용하는 방법을 중심으로 설명하며, Python 클라이언트를 이용한 예제 코드를 포함합니다.

## 1. 사전 준비 (Prerequisites)

Windows에서 서버 애플리케이션을 실행하는 가장 편리한 방법은 Docker를 사용하는 것입니다.

1.  **Docker Desktop 설치**:
    - [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)를 다운로드하여 설치합니다.
    - 설치 후 Docker Desktop을 실행하고, 터미널(PowerShell 또는 CMD)에서 `docker --version`을 입력하여 설치가 잘 되었는지 확인합니다.

2.  **Python 라이브러리 설치**:
    - Python이 설치되어 있어야 합니다.
    - 필요한 라이브러리를 설치합니다:
      ```bash
      pip install qdrant-client elasticsearch
      ```

## 2. Qdrant & Elasticsearch 설치 및 실행 (Docker Compose)

두 서비스를 한 번에 실행하기 위해 `docker-compose.yml` 파일을 생성하여 관리하는 것이 좋습니다.

**`docker-compose.yml` 파일 생성:** (프로젝트 루트 디렉토리에 생성)

```yaml
version: '3.8'

services:
  # Qdrant: 벡터 데이터베이스
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333" # REST API
      - "6334:6334" # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage

  # Elasticsearch: 검색 엔진
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false # 개발용으로 보안 비활성화 (운영 환경에서는 true 권장)
    ports:
      - "9200:9200"
    volumes:
      - ./es_data:/usr/share/elasticsearch/data
```

**실행 방법:**
터미널에서 `docker-compose.yml` 파일이 있는 디렉토리로 이동 후 아래 명령어 실행:

```bash
docker-compose up -d
```
`-d` 옵션은 백그라운드에서 실행한다는 의미입니다.

## 3. Qdrant 사용 방법 (Python 예제)

Qdrant는 벡터(Vector) 데이터를 저장하고 유사도 검색을 수행하는 데 최적화되어 있습니다.

### 기본 개념
- **Collection**: 데이터가 저장되는 단위 (RDB의 Table과 유사)
- **Point**: 저장되는 개별 데이터 (ID, Vector, Payload 포함)
- **Payload**: 벡터와 함께 저장되는 메타데이터 (JSON 형태)

### Python 코드 예제 (`example_qdrant.py`)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# 1. 클라이언트 연결
client = QdrantClient(url="http://localhost:6333")

# 2. 컬렉션 생성 (이미 있으면 삭제 후 생성)
collection_name = "my_collection"
vector_size = 4 # 예시 벡터 크기 (실제로는 임베딩 모델의 차원 수, 예: 768, 1536 등)

if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
)

# 3. 데이터 삽입 (Upsert)
points = [
    PointStruct(id=1, vector=[0.1, 0.2, 0.3, 0.4], payload={"city": "Seoul"}),
    PointStruct(id=2, vector=[0.9, 0.8, 0.7, 0.6], payload={"city": "Busan"}),
    PointStruct(id=3, vector=[0.1, 0.2, 0.3, 0.5], payload={"city": "Incheon"}),
]

client.upsert(
    collection_name=collection_name,
    points=points
)

# 4. 유사도 검색 (Search)
query_vector = [0.1, 0.2, 0.3, 0.4]
search_result = client.search(
    collection_name=collection_name,
    query_vector=query_vector,
    limit=2 # 상위 2개 결과 반환
)

print("Qdrant 검색 결과:")
for result in search_result:
    print(f"ID: {result.id}, Score: {result.score}, Payload: {result.payload}")
```

## 4. Elasticsearch 사용 방법 (Python 예제)

Elasticsearch는 텍스트 기반의 키워드 검색, 전문 검색(Full-text search)에 강력합니다.

### 기본 개념
- **Index**: 데이터가 저장되는 공간 (RDB의 Database/Table 개념)
- **Document**: 저장되는 데이터 단위 (JSON 형태)

### Python 코드 예제 (`example_es.py`)

```python
from elasticsearch import Elasticsearch

# 1. 클라이언트 연결 (Docker 설정에 맞춤)
es = Elasticsearch("http://localhost:9200")

# 연결 확인
if es.ping():
    print("Elasticsearch 연결 성공!")
else:
    print("Elasticsearch 연결 실패")

# 2. 인덱스 생성 및 데이터 삽입
index_name = "my_index"

doc1 = {"author": "kim", "text": "Elasticsearch is cool", "timestamp": "2023-10-01"}
doc2 = {"author": "lee", "text": "Python is powerful", "timestamp": "2023-10-02"}

# 데이터 삽입 (index 메소드)
es.index(index=index_name, id=1, document=doc1)
es.index(index=index_name, id=2, document=doc2)

# 데이터가 검색 가능해지도록 갱신 (테스트용, 실제 운영에선 자동 처리됨)
es.indices.refresh(index=index_name)

# 3. 키워드 검색
# 'text' 필드에 'Elasticsearch'가 포함된 문서 검색
query = {
    "match": {
        "text": "Elasticsearch"
    }
}

response = es.search(index=index_name, query=query)

print("\nElasticsearch 검색 결과:")
for hit in response['hits']['hits']:
    print(f"ID: {hit['_id']}, Source: {hit['_source']}")
```

## 5. Docker 없이 직접 설치 (Alternative)

Docker 사용이 어렵다면 바이너리 파일을 직접 다운로드하여 실행할 수 있습니다.

### Qdrant (Windows 바이너리)
1.  [Qdrant GitHub Releases](https://github.com/qdrant/qdrant/releases) 페이지로 이동합니다.
2.  최신 버전의 `qdrant-x86_64-pc-windows-msvc.zip` 파일을 다운로드합니다.
3.  압축을 풀고 `qdrant.exe`를 실행합니다.
4.  기본적으로 `http://localhost:6333`에서 실행됩니다.

### Elasticsearch (Windows Zip)
1.  [Elasticsearch 다운로드 페이지](https://www.elastic.co/kr/downloads/elasticsearch)로 이동합니다.
2.  Windows용 ZIP 파일을 다운로드합니다.
3.  압축을 풀고 `bin` 폴더로 이동합니다.
4.  `elasticsearch.bat` 파일을 실행합니다.
5.  기본적으로 `http://localhost:9200`에서 실행됩니다.
    - *주의: 최신 버전은 기본적으로 보안(HTTPS/인증)이 켜져 있어 설정이 복잡할 수 있습니다. `config/elasticsearch.yml`에서 `xpack.security.enabled: false`로 설정하면 개발용으로 쉽게 접근 가능합니다.*
