# Daiso Category Search Frontend

"어디다있소?" 다이소 매장 상품 찾기 서비스의 프론트엔드 프로젝트입니다.
React (Vite) + TailwindCSS로 구축되었습니다.

## 🛠️ 기술 스택
- **Framework**: React 18 + Vite 5
- **Styling**: TailwindCSS 3.4
- **Routing**: React Router DOM 6
- **Icons**: Lucide React

## 🚀 시작하기

### 1. 설치
의존성 패키지를 설치합니다.
```bash
cd frontend
npm install
```

### 2. 개발 서버 실행
로컬 개발 서버를 시작합니다.
```bash
npm run dev
```
브라우저에서 `http://localhost:5173`으로 접속하여 확인합니다.

## 📂 프로젝트 구조
- `src/components`: 공통 컴포넌트 (Header, Layout, Button, Input)
- `src/pages`: 주요 페이지 (Home, VoiceSearch, SearchResults, MapNavigation, NoResult)
- `src/lib`: 유틸리티 함수

## 🎨 디자인
다이소 브랜드 컬러(Red: `#E31937`)를 기반으로 한 깔끔한 키오스크 UI입니다.
- **Home**: 음성/텍스트 검색 진입점
- **VoiceSearch**: 음성 인식 시뮬레이션 화면
- **SearchResults**: 상품 목록 및 위치 안내 버튼
- **MapNavigation**: 매대 위치 지도 및 모바일 QR 연동
