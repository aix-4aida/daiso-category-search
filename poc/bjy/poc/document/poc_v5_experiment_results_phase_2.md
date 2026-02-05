# PoC v5 Phase 2 실험 결과 보고서: AR 네비게이션 구현

- **날짜**: 2026-01-27
- **목표**: PoC v4의 단순 방향 지시를 넘어, **현실 배경(Camera) 위에 정보가 결합된 AR 경험**을 구현하고, 안드로이드/iOS 간 파편화된 센서 로직을 통합한다.

## 1. 구현 기능 (Features)

### 📸 AR View (Camera Background)
- **구현**: HTML5 `<video>` 태그와 `navigator.mediaDevices.getUserMedia({ facingMode: 'environment' })` API 사용.
- **결과**: 모바일 웹 브라우저에서도 별도 앱 설치 없이 후면 카메라를 배경으로 사용하여 **현실감 있는 길안내** 가능. (HTTPS 필수)

### 🧭 Robust Compass (센서 보정)
- **문제 해결**:
    - **Android**: `alpha` 값이 반시계 방향(CCW)으로 증가하는 문제를 발견. `(360 - e.alpha)` 연산을 통해 시계 방향(CW)인 실제 방위각(True Heading)으로 변환.
    - **Jittering**: 센서 데이터의 미세한 떨림을 잡기 위해 **Low-pass Filter (Smoothing)** 적용. (`lastHeading + diff * 0.1`)
- **결과**: 사용자가 몸을 돌려도 화살표가 **목표 지점(절대 좌표)을 끈질기게 가리키는(World-Locking)** 효과 구현 성공.

### 🖼️ UI Overlay
- **정보 표시**: 상단에 반투명 카드 UI로 `상품명`과 `거리(남은 거리)` 표시.
- **시각화**: 단순 2D 화살표 대신, **3D 스타일의 SVG 화살표**와 **목표 방위각(Target Bearing) 시각화** 추가.

## 2. PoC v4 vs PoC v5 비교 (달라진 점)

| 구분 | PoC v4 (Phase 2) | **PoC v5 (Phase 2)** | 비고 |
| :--- | :--- | :--- | :--- |
| **배경 (View)** | 흰색 빈 화면 (White BG) | **실시간 카메라 (Real-world AR)** | 몰입감 대폭 상승 |
| **방향 지시** | 단순 회전 (Relative Rotation) | **절대 방위각 추적 (World-Locking)** | 안드로이드 센서 이슈 해결 |
| **정보 전달** | 단순 텍스트 | **UI Overlay (Glassmorphism)** | 시인성 개선 |
| **센서 로직** | 기본 API 사용 (최적화 X) | **Smoothing & Calibration 적용** | 떨림 보정, 정밀도 향상 |

## 3. PoC v5 종합 성과 요약 (Phase 1 Search + Phase 2 AR)

Phase 1(검색 지능화)과 Phase 2(AR 시각화)의 통합 성과는 다음과 같습니다.

| 모듈 (Module) | 항목 (Item) | PoC v4 (기존) | **PoC v5 (개선)** | 비고 (Note) |
| :--- | :--- | :--- | :--- | :--- |
| **Search Engine** | **정확도 (Accuracy)** | 약 70% (추정) | **93.4% (57/61 성공)** | **목표(90%) 초과 달성** |
| (Phase 1) | **검색 로직** | 단순 LLM Prompt | **Few-Shot + CoT (추론 강화)** | 복합/추상적 질의 해결 |
| | **테스트 데이터** | 20개 (단순 대화형) | **61개 (Hard Cases)** | 유의어/오타/시각적 묘사 커버 |
| **AR Navigation** | **배경 (View)** | 흰색 빈 화면 | **실시간 카메라 (Live Feed)** | 현실감/몰입감 증대 |
| (Phase 2) | **나침반 (Compass)** | 단순 회전 (불안정) | **보정(Smoothing) + World-Locking** | 떨림 없는 정확한 길안내 |
| | **UI/UX** | 단순 텍스트 | **AR Overlay + 3D Arrow** | 직관적 정보 전달 |

## 4. 결론
PoC v5는 단순한 '기능 구현'을 넘어 **'사용자 경험(UX)'을 상용화 수준**으로 끌어올렸습니다.
특히 **Web AR 기술**만으로 앱 수준의 네비게이션을 구현할 수 있음을 증명했으며, 이는 키오스크에서 별도 앱 설치 없이 QR만으로 즉시 서비스를 이용해야 하는 마트 환경에 최적화된 접근입니다.

다음 단계(Phase 3)인 **TTS(음성 안내)**가 결합되면 시각+청각이 결합된 완벽한 멀티모달 가이드가 완성될 것입니다.
