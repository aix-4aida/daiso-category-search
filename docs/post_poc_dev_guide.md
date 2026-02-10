# 어디다있소 개발 및 배포 가이드 (Post-PoC)

본 문서는 사용자의 질문에 대한 답변과 향후 진행할 작업에 대한 구체적인 가이드를 포함합니다.

---

## 2. 스트레스 테스트 및 아키텍처 설계 근거 (Why?)

### 2.1. 왜 스트레스 테스트를 해야 하는가?
시스템이 실제 환경에서 견딜 수 있는지 **'검증'**하는 과정입니다.
1.  **안정성 확보**: 예상치 못한 트래픽 폭주 시 시스템이 다운되지 않고 버티는지(Availability) 확인합니다.
2.  **SLA(Service Level Agreement) 검증**: "검색 결과는 3초 이내에 나와야 한다"는 약속을 95% 이상(P95) 지킬 수 있는지 수치로 증명합니다.
3.  **병목 구간 발견**: CPU가 부족한지, DB 연결이 느린지, 외부 API(STT 등)가 범인인지 찾아내어 최적화 포인트를 찾습니다.

### 2.2. 왜 트래픽 위주로 아키텍처 요구사항을 정의했는가?
소프트웨어 아키텍처는 **비용**과 **성능** 사이의 균형을 맞추는 설계도입니다.
1.  **적정 인프라 사이징**: 트래픽(QPM, 동시접속자)을 모르면, 너무 비싼 서버(돈 낭비)를 쓰거나 너무 약한 서버(서비스 장애)를 쓰게 됩니다.
2.  **기술 스택 결정**: 
    - 트래픽이 적다면? → 단순한 Monolithic 구조 (개발 빠름, 관리 쉬움).
    - 트래픽이 폭발적이라면? → MSA, Serverless, Auto-scaling, Caching, Queue 도입 필요.
3.  **확장성 설계**: 향후 사용자가 늘어날 때 어디를 늘려야(Scale-out) 할지 미리 계획하기 위함입니다.

---

## 3. UX/UI 및 웹 구현 결과
제공해주신 UX 가이드라인(v3.0)과 디자인 시안을 반영하여 구현을 완료했습니다.

-   **Tech Stack**: HTML5, Vanilla CSS, Vanilla JS (가볍고 빠른 로딩 속도 중시).
-   **Design System**: `css/style.css`에 컬러 변수(`--color-primary`) 및 컴포넌트 스타일 정의.
-   **Interactive Elements**: 로딩 애니메이션, QR 코드 생성, 상세 페이지(모바일 뷰) 구현.
-   **Special Design**: 로고 '있' 자에 상단 빨강/하단 검정 그라데이션 적용 완료.

---

## 4. [실습] 지금 당장 해야 할 일 (Action Plan)

아래 순서대로 따라하시면 **End-to-End 배포 및 검증**을 완료할 수 있습니다.

### Step 1: 로컬에서 스트레스 테스트 맛보기
AWS에 올리기 전에, 로컬 환경에서 테스트 스크립트가 잘 도는지 확인합니다.

1.  **백엔드 서버 실행** (터미널 1)
    ```powershell
    # backend 폴더가 있는 루트 디렉토리에서
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    ```

2.  **스트레스 테스트 실행** (터미널 2)
    ```powershell
    # 60 QPM (초당 1건)으로 30초간 테스트
    python tests/stress_test_qpm.py --url http://localhost:8000 --qpm 60 --duration 30
    ```
3.  **결과 확인**: `SLA (P95 < 3s)`가 PASS인지, `latency_ms` 평균이 얼마인지 확인합니다.

### Step 2: AWS Lightsail 컨테이너 서비스 생성
가장 쉽고 빠르게 배포할 수 있는 방법입니다.

1.  [AWS Lightsail 콘솔](https://lightsail.aws.amazon.com/) 접속.
2.  **Containers** 탭 클릭 -> **Create container service**.
3.  **Size**: **Micro** ($10/월) 또는 **Small** ($15/월) 선택.
    > **🤔 어떤 크기를 선택해야 할까요?**
    >
    > | 구분 | **Nano / Micro** ($7~$10) | **Small / Medium** ($15~$40) |
    > | :--- | :--- | :--- |
    > | **추천 상황** | **개발/테스트**, 개인 포트폴리오 | **실제 운영**, 팝업스토어 배포 |
    > | **동시 접속자** | 1~5명 수준 | 10~50명 수준 |
    > | **QPM (분당 쿼리)** | ~60 QPM (초당 1건 미만) | 60+ QPM (초당 1건 이상) |
    > | **메모리(RAM)** | 512MB ~ 1GB (조금 빠듯함) | 2GB ~ 4GB (여유로움) |
    >
    > *💡 **Tip**: 처음엔 **Micro**로 시작하고, 느려지면 클릭 몇 번으로 스펙을 올릴(Scale-up) 수 있습니다.*
    >
    > **Scale (인스턴스 개수)**: **1개**로 시작하세요.
    > - 개발/테스트 단계에서는 1개면 충분합니다.
    > - 나중에 실제 운영 시 '고가용성(무중단 배포)'이 필요하면 2개 이상으로 늘리면 됩니다.
4.  **Region**: Seoul (ap-northeast-2).
5.  **Service Name**: `daiso-search-service` 입력 -> **Create service**.

### Step 3: Docker 이미지 빌드 및 푸시 (로컬 PC에서)
AWS CLI와 Lightsail 플러그인이 설치되어 있어야 합니다. (없다면 설치 필요)
*설치가 번거롭다면, 코드를 Github에 올리고 Lightsail에서 Github 연동 배포를 하는 방법도 있습니다.*

**방법 A: 로컬 빌드 후 푸시 (AWS CLI 필요) - 🔥 강력 추천**
> **왜 추천하나요?**
> - 내 컴퓨터에서 잘 돌아가는지 확인하고 바로 올릴 수 있어 **가장 확실**합니다.
> - Github 연동 방식은 `Action` 설정 등 초기 세팅이 복잡할 수 있습니다.
> - **CLI 설치**: [AWS CLI 설치 페이지](https://aws.amazon.com/cli/) 또는 **[Windows용 직접 다운로드 링크(.msi)](https://awscli.amazonaws.com/AWSCLIV2.msi)**를 클릭하여 설치하세요. 설치 후 터미널(Powershell)을 껐다 켜고 `aws configure`를 입력하면 됩니다.
> - **[중요] Lightsail 플러그인 설치**: 컨테이너 배포를 위해 **[`lightsailctl` 플러그인(Windows용 .exe)](https://s3.us-west-2.amazonaws.com/lightsailctl/latest/windows-amd64/lightsailctl.exe)**을 다운로드해서, `C:\Program Files\Amazon\AWSCLIV2\` 폴더(또는 PATH가 잡힌 곳)에 넣어주셔야 합니다. 
>   - *팁: 위 exe 파일이 번거롭다면 [Windows용 설치 프로그램(.msi)](https://s3.us-west-2.amazonaws.com/lightsailctl/latest/windows-amd64/lightsailctl.msi)을 받아 설치하는 것이 가장 편합니다.*

> - **설정 방법 (`aws configure`)**:
>   1.  **Access Key ID**: AWS 콘솔 -> 우측 상단 계정명 클릭 -> **[보안 자격 증명(Security Credentials)]** -> **[액세스 키 만들기]**에서 생성한 키(AKIA...)를 입력합니다.
>   2.  **Secret Access Key**: 위에서 키를 만들 때 같이 나오는 비밀키를 입력합니다. (이때만 볼 수 있으니 꼭 복사해두세요!)
>   3.  **Default region name**: `ap-northeast-2` (서울) 입력.
>   4.  **Default output format**: `json` 입력.

```powershell
# 0. 프로젝트 폴더로 이동 (매우 중요! 관리자 권한으로 열면 System32일 수 있음)
cd c:\Users\301\pjt\Final\search\daiso-category-search

# 1. 먼저 Docker 이미지를 빌드합니다. (이 단계가 빠져서 에러가 났을 수 있습니다!)
docker build -t daiso-backend:latest .
docker build -f Dockerfile.frontend -t daiso-frontend:latest .

# 2. AWS 로그인 및 푸시
aws lightsail push-container-image --service-name daiso-search-service --label backend --image daiso-backend:latest
aws lightsail push-container-image --service-name daiso-search-service --label frontend --image daiso-frontend:latest
```

**방법 B: Dockerfile 기반 직접 배포 (권장)**
단순하게 Python/Node 환경만 필요하다면, Lightsail 콘솔에서 **Deploy** 탭 -> **Create deployment** 를 통해 이미지를 지정하거나 로컬 이미지를 올립니다.


> **⚠️ 에러 발생 시 확인사항 ("error during connect...")**
> 1.  **Docker Desktop이 실행 중인가요?** (화면 우측 하단 트레이 아이콘에 고래가 보여야 합니다.)
> 2.  **PowerShell을 관리자 권한으로 실행했나요?** (Start 메뉴 -> PowerShell 우클릭 -> 관리자로 실행)
> 3.  먼저 `docker ps`를 입력해서 에러 없이 빈 목록이라도 나오는지 확인해보세요.

### Step 4: End-to-End 동작 확인
배포가 완료되면 Lightsail에서 `Public Domain` 주소를 줍니다.

1.  **접속**: 브라우저로 `https://<your-service-url>` 접속.
2.  **검색 테스트**: '냄비', '화장지' 등 검색.
3.  **스트레스 테스트 (Real World)**:
    ```powershell
    python tests/stress_test_qpm.py --url https://<your-service-url> --qpm 60 --duration 60
    ```
    이것이 진짜 **QPM 테스트**입니다.

---

## 5. 파일 위치 및 참고
- **스트레스 테스트 스크립트**: `tests/stress_test_qpm.py`
- **백엔드 소스**: `backend/`
- **프론트엔드 소스**: `frontend/`
- **UX/UI 스타일**: `frontend/css/style.css`
