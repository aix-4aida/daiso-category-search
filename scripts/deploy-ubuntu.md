# Ubuntu 22.04 배포 가이드 (AWS Lightsail)

> **환경:** Ubuntu 22.04 LTS, 1 vCPU, 512MB RAM
> **정책:** No Docker - 모든 서비스 네이티브 프로세스로 구동
> **프로세스 관리:** PM2 (Backend, Qdrant), systemd (Elasticsearch)

---

## 0. 서버 초기 설정

### 0-1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

### 0-2. Swap 설정 (필수 - 512MB 환경)
```bash
# 2GB Swap 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 적용
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Swappiness 조정 (메모리 부족 시 적극적으로 Swap 사용)
echo 'vm.swappiness=60' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 확인
free -h
```

### 0-3. 필수 패키지 설치
```bash
sudo apt install -y curl wget unzip git build-essential
```

---

## 1. Java 설치 (Elasticsearch용)

```bash
# OpenJDK 11 설치 (ES 7.x 권장)
sudo apt install -y openjdk-11-jre-headless

# 확인
java -version
```

---

## 2. Elasticsearch 7.x 설치

### 2-1. 다운로드 & 설치
```bash
ES_VERSION="7.17.27"

cd /opt
sudo wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz
sudo tar -xzf elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz
sudo rm elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz
sudo mv elasticsearch-${ES_VERSION} elasticsearch
```

### 2-2. 전용 사용자 생성
```bash
sudo useradd -r -s /bin/false elasticsearch
sudo chown -R elasticsearch:elasticsearch /opt/elasticsearch
```

### 2-3. JVM 메모리 제한 (필수)
```bash
sudo sed -i 's/-Xms[0-9]*[gm]/-Xms128m/' /opt/elasticsearch/config/jvm.options
sudo sed -i 's/-Xmx[0-9]*[gm]/-Xmx128m/' /opt/elasticsearch/config/jvm.options
```

### 2-4. elasticsearch.yml 설정
```bash
cat <<'EOF' | sudo tee -a /opt/elasticsearch/config/elasticsearch.yml

# Daiso Kiosk Config
cluster.name: daiso-search
node.name: daiso-node-1
network.host: 127.0.0.1
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false

# 메모리 절약
indices.memory.index_buffer_size: 10%
thread_pool.write.queue_size: 200
EOF
```

### 2-5. systemd 서비스 등록
```bash
cat <<'EOF' | sudo tee /etc/systemd/system/elasticsearch.service
[Unit]
Description=Elasticsearch 7.x
Documentation=https://www.elastic.co
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=elasticsearch
Group=elasticsearch
Environment=ES_HOME=/opt/elasticsearch
Environment=ES_PATH_CONF=/opt/elasticsearch/config
ExecStart=/opt/elasticsearch/bin/elasticsearch
Restart=on-failure
RestartSec=10
LimitNOFILE=65535
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

### 2-6. 확인
```bash
# 시작까지 30초 정도 소요
sleep 30
curl http://localhost:9200
sudo systemctl status elasticsearch
```

---

## 3. Qdrant 설치

### 3-1. 다운로드
```bash
QDRANT_VERSION="1.13.2"

sudo mkdir -p /opt/qdrant
cd /opt/qdrant
sudo wget https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-musl.tar.gz
sudo tar -xzf qdrant-x86_64-unknown-linux-musl.tar.gz
sudo rm qdrant-x86_64-unknown-linux-musl.tar.gz
sudo chmod +x qdrant
```

### 3-2. Qdrant 설정 (메모리 절약)
```bash
cat <<'EOF' | sudo tee /opt/qdrant/config/config.yaml
storage:
  storage_path: /opt/qdrant/storage
  on_disk_payload: true

service:
  host: 127.0.0.1
  http_port: 6333
  grpc_port: 6334

log_level: WARN
EOF
```

### 3-3. 전용 사용자 & 권한
```bash
sudo useradd -r -s /bin/false qdrant
sudo chown -R qdrant:qdrant /opt/qdrant
```

### 3-4. systemd 서비스 등록 (PM2 대신 systemd 통일도 가능)
```bash
cat <<'EOF' | sudo tee /etc/systemd/system/qdrant.service
[Unit]
Description=Qdrant Vector Database
After=network-online.target

[Service]
Type=simple
User=qdrant
Group=qdrant
WorkingDirectory=/opt/qdrant
ExecStart=/opt/qdrant/qdrant
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable qdrant
sudo systemctl start qdrant
```

### 3-5. 확인
```bash
curl http://localhost:6333
```

---

## 4. Python 3.12 + Backend 설치

### 4-1. Python 3.12 설치
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

### 4-2. Poetry 설치
```bash
curl -sSL https://install.python-poetry.org | python3.12 -
# PATH 추가
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
poetry --version
```

### 4-3. 프로젝트 클론 & 의존성 설치
```bash
cd /home/ubuntu
git clone <YOUR_REPO_URL> daiso-category-search
cd daiso-category-search/backend

# Python 3.12 사용하도록 설정
poetry env use python3.12
poetry install --without dev
```

### 4-4. 환경변수 설정
```bash
cp /home/ubuntu/daiso-category-search/.env.example /home/ubuntu/daiso-category-search/.env

# .env 편집
nano /home/ubuntu/daiso-category-search/.env
```

`.env` 내용:
```env
GOOGLE_API_KEY=AIzaSy...실제키
ELASTIC_URL=http://127.0.0.1:9200
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=changeme
QDRANT_URL=http://127.0.0.1:6333
APP_ENV=production
```

---

## 5. Frontend 빌드

### 5-1. Node.js 22 설치
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v && npm -v
```

### 5-2. 빌드
```bash
cd /home/ubuntu/daiso-category-search/frontend
npm ci
npx tsc -b && npx vite build
# 결과물: frontend/dist/
```

빌드 후 `frontend/dist/`가 생성되면 FastAPI가 자동으로 SPA를 서빙합니다 (`main.py`에 이미 설정됨).

---

## 6. PM2로 FastAPI 관리

### 6-1. PM2 설치
```bash
sudo npm install -g pm2
```

### 6-2. ecosystem 설정 파일 생성
```bash
cat <<'EOF' > /home/ubuntu/daiso-category-search/ecosystem.config.cjs
module.exports = {
  apps: [
    {
      name: "daiso-backend",
      cwd: "/home/ubuntu/daiso-category-search/backend",
      script: "poetry",
      args: "run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1",
      interpreter: "none",
      env: {
        APP_ENV: "production",
      },
      max_memory_restart: "200M",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: "/home/ubuntu/logs/backend-error.log",
      out_file: "/home/ubuntu/logs/backend-out.log",
    },
  ],
};
EOF

mkdir -p /home/ubuntu/logs
```

### 6-3. 시작 & 자동 재시작 등록
```bash
cd /home/ubuntu/daiso-category-search
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup systemd
# 출력되는 sudo 명령어를 복사해서 실행
```

### 6-4. 확인
```bash
pm2 status
pm2 logs daiso-backend --lines 20
curl http://localhost:8000/api/health
```

---

## 7. Nginx 리버스 프록시 (선택)

외부에서 80/443 포트로 접근하려면 Nginx를 앞에 둡니다.

### 7-1. 설치
```bash
sudo apt install -y nginx
```

### 7-2. 설정
```bash
cat <<'EOF' | sudo tee /etc/nginx/sites-available/daiso
server {
    listen 80;
    server_name _;  # 도메인이 있으면 여기에 입력

    # 요청 크기 제한 (이미지 업로드 등)
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 지원 (필요 시)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/daiso /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7-3. HTTPS (Let's Encrypt) - 도메인이 있는 경우
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
# 이후 자동 갱신 확인
sudo certbot renew --dry-run
```

---

## 8. 방화벽 설정

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

> **주의:** ES(9200), Qdrant(6333)은 외부에 열지 않습니다. `127.0.0.1`에만 바인딩되어 있습니다.

---

## 9. 배포 후 전체 확인

```bash
# 서비스 상태
sudo systemctl status elasticsearch
sudo systemctl status qdrant
pm2 status

# 포트 확인
ss -tlnp | grep -E '9200|6333|8000|80'

# API 확인
curl http://localhost:9200          # ES
curl http://localhost:6333          # Qdrant
curl http://localhost:8000/api/health  # Backend
curl http://localhost                  # Nginx → SPA
```

---

## 10. 메모리 모니터링

512MB 환경에서는 메모리 관리가 핵심입니다.

```bash
# 실시간 모니터링
watch -n 5 free -h

# 프로세스별 메모리
ps aux --sort=-%mem | head -10

# 예상 메모리 분배:
# ES JVM:     ~128MB
# Qdrant:     ~50-100MB
# Python/UV:  ~80-150MB
# Nginx:      ~5MB
# OS:         ~100MB
# -----------------------
# 합계:       ~400-500MB (Swap으로 버퍼)
```

---

## 11. 업데이트 배포 (이후)

```bash
cd /home/ubuntu/daiso-category-search
git pull origin dev

# Frontend 재빌드
cd frontend && npm ci && npx tsc -b && npx vite build && cd ..

# Backend 의존성 갱신 & 재시작
cd backend && poetry install --without dev && cd ..
pm2 restart daiso-backend

# 확인
pm2 logs daiso-backend --lines 10
```

---

## 서비스 시작 순서 요약

| 순서 | 서비스 | 관리 방식 | 포트 | 바인딩 |
|------|--------|-----------|------|--------|
| 1 | Elasticsearch | systemd | 9200 | 127.0.0.1 |
| 2 | Qdrant | systemd | 6333 | 127.0.0.1 |
| 3 | FastAPI (Uvicorn) | PM2 | 8000 | 0.0.0.0 |
| 4 | Nginx | systemd | 80/443 | 0.0.0.0 |

> ES와 Qdrant는 systemd `After=network-online.target`으로 부팅 시 자동 시작됩니다.
> PM2는 `pm2 startup`으로 등록하면 부팅 시 자동 시작됩니다.
