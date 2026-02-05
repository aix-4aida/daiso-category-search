sequenceDiagram
    autonumber
    actor User as 👤 사용자
    participant Kiosk as 🖥️ 키오스크 (Tablet)
    participant Server as 🧠 서버 (Agent)
    participant LLM as ✨ Gemini (Logic)
    participant DB as 🗄️ 검색엔진 (Vector/DB)
    participant Mobile as 📱 모바일 웹앱 (WebAR)
    participant Marker as 🔳 중간 마커 (QR)

    %% [Phase 1] 키오스크 검색 및 추론
    rect rgb(240, 240, 240)
        Note over User, Kiosk: "이거.. 튀김 건지는 망 어디 있어?" (음성)
        User->>Kiosk: 음성 발화 (STT 변환)
        Kiosk->>Server: 텍스트 쿼리 전송

        Note right of Server: ① 의도 파악 & 의미 추출
        Server->>LLM: "상품 찾기 질문인가? 검색 키워드는?"
        LLM-->>Server: {intent: true, keywords: ["채반", "뜰채"]}

        Note right of Server: ② 하이브리드 검색 & 순위 조정
        par Parallel Search
            Server->>DB: 키워드 검색 (BM25)
            Server->>DB: 벡터 검색 (Embedding)
        end
        DB-->>Server: 후보 리스트 반환
        Server->>LLM: "사용자 의도에 맞는 Top-1 선정해줘"
        LLM-->>Server: {product: "스텐 채반", loc: "Zone-C, Shelf-4"}
    end

    %% [Phase 2] 결과 표출 및 모바일 이관 (Handoff)
    rect rgb(255, 248, 220)
        Note right of Kiosk: ③ 지도 표시 & 연결 QR 생성
        Server-->>Kiosk: 상품 정보 + 좌표(x:15, y:40) + 지도 데이터
        
        Kiosk->>Kiosk: 매장 전체 지도 표시 (Macro View)
        Kiosk->>Kiosk: Handoff QR 생성 (URL: /nav?target=15,40&start=kiosk_1)
        Kiosk-->>User: "2층 C구역입니다. QR로 안내를 이어받으세요."
    end

    %% [Phase 3] 모바일 하이브리드 내비게이션
    rect rgb(225, 255, 225)
        Note right of Mobile: ④ AR 주행 시작
        User->>Mobile: 키오스크 QR 스캔 (웹앱 실행)
        Mobile->>Mobile: 초기 위치 설정 (Start: Kiosk, End: Zone-C)

        loop 센서 추적 (PDR)
            Mobile->>Mobile: 나침반(방향) + 가속도(걸음) 감지
            Mobile-->>User: AR 화살표 & 지도 UI 갱신
        end

        opt ⑤ 위치 오차 보정 (Correction)
            User->>User: "위치가 안 맞네?" (중간 기둥 QR 발견)
            User->>Marker: 보정용 QR 스캔
            Marker-->>Mobile: 절대 좌표값 (ex: Zone-B Pillar)
            Mobile->>Mobile: 현재 위치 강제 동기화 (Recalibration)
            Mobile-->>User: "위치 보정 완료. 경로 재탐색"
        end

        Mobile-->>User: "목적지 도착!" (안내 종료)
    end