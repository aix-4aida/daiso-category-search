# PoC v4 Phase 2 실험 결과 보고서: 생성 경험 검증

## 개요
- **목표**: 키오스크(Mock Data)에서 생성된 검색 결과가 QR 코드를 통해 모바일로 끊김 없이 전달(Migration)되고, 모바일 웹에서 센서를 활용한 길 안내가 작동하는지 검증.
- **기간**: 2026-01-27
- **검증 환경**:
    - **Host**: Local Python HTTP Server (Port 8000)
    - **Tunneling**: Ngrok (External HTTPS Access)
    - **Devices**: Windows PC (Kiosk), Smartphone (Mobile)

## 구현 결과물
1.  **Frontend**: `poc/frontend/phase_2/`
    - `kiosk.html`: 상품 정보 표시 및 동적 QR 코드 생성 (모바일 URL 파라미터 인코딩).
    - `mobile.html`: URL 파라미터 파싱 및 DeviceOrientation API를 이용한 나침반 화살표 구현.
    - `arrow.png`: SVG로 대체 구현 (이미지 의존성 제거).

## 검증 시나리오 및 결과
| 단계 | 시나리오 | 기대 결과 | 실제 결과 | 판정 |
| :--- | :--- | :--- | :--- | :--- |
| **1. Kiosk** | PC 브라우저에서 Ngrok URL로 접속 | 화면에 상품명("스텐 채반")과 QR 코드가 정상 렌더링됨. | ✅ 렌더링 성공 | **PASS** |
| **2. Handover** | 스마트폰으로 QR 코드 스캔 | 모바일 브라우저가 열리며 URL에 `?name=스텐...` 등 파라미터가 포함됨. | ✅ 파라미터 전달 성공 | **PASS** |
| **3. Mobile** | "안내 시작하기" 버튼 클릭 및 폰 회전 | 사용자의 방향에 따라 화살표가 목표 지점(가상 좌표)을 향해 회전함. | ✅ 센서 연동/회전 성공 | **PASS** |

## 결론
**"데이터의 이사(Data Migration)"** 및 **"센서 기반 경험(Experience)"** 검증 완료.
- 별도의 DB 연동 없이 URL 파라미터만으로도 키오스크-모바일 간 데이터 연동이 매끄럽게 이루어짐을 확인.
- Ngrok을 통한 외부 접속 및 iOS 동작 확인 완료.
- 다음 단계(Real Backend Integration) 진행 가능.
