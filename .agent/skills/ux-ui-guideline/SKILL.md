---
name: daiso-ui-system
description: 다이소 매장 안내 서비스 "어디다있소"의 UI를 생성합니다. 
  프론트엔드 화면 구현, 컴포넌트 생성, CSS 스타일링, 레이아웃 작업 시 사용. 
  Use when building UI, creating components, styling pages, or generating HTML/CSS.
---

# 어디다있소 UX/UI 디자인 시스템

## 컬러 규칙
모든 색상은 CSS custom property로 참조할 것. 하드코딩 금지.

| 토큰 | 색상 | 용도 |
|------|------|------|
| `--color-primary` | `#E50000` | 브랜드 빨강, CTA 버튼, 로고 강조 |
| `--color-primary-light` | `#FFEBEB` | 카드 배경, 선택 하이라이트 |
| `--color-bg` | `#FFFFFF` | 페이지 배경 |
| `--color-bg-light` | `#F5F5F5` | 섹션 구분 배경 |
| `--color-text` | `#333333` | 본문 텍스트 |
| `--color-text-light` | `#888888` | 보조 텍스트, 가격 |
| `--color-border` | `#E0E0E0` | 카드/섹션 테두리 |
| `--color-map-path` | `#2962FF` | 지도 이동경로 (파란 점선) |
| `--color-map-pin` | `#E50000` | 지도 위치 마커 |

## 타이포그래피
기본 폰트: SUIT 사용할 것. fallback: 'Noto Sans KR', sans-serif

웹폰트 적용 시 아래 CDN 링크를 HTML head에 추가할 것:
<link href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/variable/woff2/SUIT-Variable.css" rel="stylesheet">

CSS에서는 다음과 같이 지정할 것:
font-family: 'SUIT Variable', sans-serif;

- h1: 28px, Bold (font-weight: 700)
- h2: 20px, SemiBold (font-weight: 600)
- 본문: 16px, Regular (font-weight: 400)
- 보조: 14px, Regular, --color-text-light
- 가격: 16px, Bold (font-weight: 700), --color-primary

## 버튼 생성 규칙
| 유형 | 스타일 |
|------|--------|
| Primary | 빨간 배경 (#E50000), 흰 텍스트, border-radius: 25px |
| Secondary | 흰 배경, 빨간 테두리 1px, 빨간 텍스트, border-radius: 25px |
| Tab (활성) | 빨간 텍스트, 하단 빨간 인디케이터 |
| Tab (비활성) | 회색 텍스트 |

## 카드 생성 규칙
- 배경: 흰색
- 테두리: 1px solid #E0E0E0
- border-radius: 12px
- 그림자: 0 2px 8px rgba(0,0,0,0.08)
- 선택 상태: 좌측 4px 빨간 보더

## 마이크 버튼 규칙
- 크기: 80px 원형
- 배경: 그라디언트 빨강
- 아이콘: 흰색 마이크
- 대기 상태: 그림자만
- 녹음 중: 바깥 파동 애니메이션 (빨강 반투명 원 확산)

## 지도 규칙
- 배경: frontend/images/map_b1.png (B1), map_b2.png (B2) 이미지 사용할 것
- 지도는 직접 그리지 말고, 평면도 이미지 위에 마커와 경로를 오버레이할 것
- 경로 생성 시 반드시 waypoint 노드를 따라 그릴 것. 매대 블록을 관통하는 직선 경로 금지.
- 경로 탐색 데이터: [map-pathfinding.md](references/map-pathfinding.md) 참조
- 최단 경로 알고리즘: waypoint 그래프에서 BFS 또는 Dijkstra 적용
- 이동 경로: --color-map-path 파란 점선 (stroke-dasharray), SVG로 오버레이
- 현재 위치: 파란 원 (파동 효과)
- 상품 위치: --color-map-pin 빨간 핀 마커

## 로고 규칙
- 서비스명: "어디다있소"
- 로고는 SVG 또는 이미지 파일로 처리할 것 (텍스트 렌더링 금지)
- 색상 구성: "어디" = 검정, "다" = 빨강, "있"의 'ㅇ'+'ㅣ' = 빨강 / 'ㅆ' = 검정, "소" = 빨강
- 좌측에 다이소 로고 아이콘 (빨간 사각형) 배치 가능

## 레이아웃 판단 기준
- "키오스크", "태블릿" 언급 → 1024px+ 좌우 분할 레이아웃, 하단 탭
- "모바일" 언급 → ~768px 단일 컬럼, 하단 버튼
- 명시하지 않은 경우 → 사용자에게 먼저 물어볼 것

## 반응형 기준

| 디바이스 | 해상도 | 레이아웃 |
|---------|--------|---------|
| 태블릿 (키오스크) | 1024px+ | 좌우 분할, 하단 탭 |
| 모바일 | ~768px | 단일 컬럼, 하단 버튼 |

## 상세 화면 스펙
각 화면의 구체적 구성요소는 아래 참조:
- 6개 핵심 화면 스펙: [screen-specs.md](references/screen-specs.md)
- User Flow (4 Stage): [user-flow.md](references/user-flow.md)