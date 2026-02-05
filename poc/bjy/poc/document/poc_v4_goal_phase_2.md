**"데이터의 이사(Migration)"**입니다. Step 1에서 LLM이 만든 JSON 데이터가 키오스크 화면에 예쁘게 뜨고, QR을 통해 사용자의 폰으로 끊김 없이 넘어가는지를 눈으로 확인하는 것이 목표


/poc/frontend
  ├── kiosk.html      (키오스크 화면: 결과 표시 + QR 생성)
  ├── mobile.html     (모바일 화면: 나침반 + 길 안내)
  ├── arrow.png       (화살표 이미지: 구글에서 아무거나 다운로드)
  └── map_dummy.jpg   (매장 지도 이미지: 아무거나)


1. 키오스크 화면 (kiosk.html)
이 파일은 "Step 1의 결과물(JSON)"을 받아서 보여주는 역할을 합니다. 지금은 JSON을 코드 안에 박아넣습니다(Mocking).

기능: 상품 위치(target_x, y)를 URL 파라미터로 변환하여 QR코드로 굽습니다.

HTML:
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Search-Roca Kiosk</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; }
        .result-box { border: 2px solid #ddd; padding: 20px; border-radius: 10px; display: inline-block; }
        #qrcode { margin-top: 20px; display: flex; justify-content: center; }
        h1 { color: #d63031; } /* 다이소 빨간색 */
    </style>
</head>
<body>

    <div class="result-box">
        <h1 id="product-name">상품명 로딩중...</h1>
        <p id="tts-text">안내 멘트 로딩중...</p>
        <hr>
        <h3>👇 스마트폰으로 스캔하여 길안내 받기</h3>
        <div id="qrcode"></div>
    </div>

    <script>
        // [Step 1 결과물] 가상 데이터 (LLM이 줬다고 가정)
        const mockData = {
            "product_name": "스텐 건지기 (채반)",
            "location_info": { "zone": "Kitchen_A", "x": 150, "y": 400 }, // 목표 좌표
            "tts_text": "2층 주방코너 A구역에 있습니다. QR을 찍어보세요."
        };

        // 1. 화면에 정보 뿌리기
        document.getElementById("product-name").innerText = mockData.product_name;
        document.getElementById("tts-text").innerText = mockData.tts_text;

        // 2. 모바일로 넘길 URL 생성 (핵심!)
        // ★중요★: 나중에 실제 호스팅 주소로 바꿔야 함 (지금은 로컬 테스트용)
        const mobileBaseUrl = window.location.href.replace("kiosk.html", "mobile.html");
        
        // 파라미터 인코딩: ?tx=150&ty=400&name=채반
        const finalUrl = `${mobileBaseUrl}?tx=${mockData.location_info.x}&ty=${mockData.location_info.y}&name=${encodeURIComponent(mockData.product_name)}`;

        console.log("Generated URL:", finalUrl);

        // 3. QR 코드 생성
        new QRCode(document.getElementById("qrcode"), {
            text: finalUrl,
            width: 200,
            height: 200
        });
    </script>
</body>
</html>


좋습니다! Step 2: 경험 검증 (Experience Validation) 단계입니다.

이 단계의 핵심은 **"데이터의 이사(Migration)"**입니다. Step 1에서 LLM이 만든 JSON 데이터가 키오스크 화면에 예쁘게 뜨고, QR을 통해 사용자의 폰으로 끊김 없이 넘어가는지를 눈으로 확인하는 것이 목표입니다.

복잡한 서버 구축 없이, **HTML 파일 2개(kiosk.html, mobile.html)**만으로 이 마법 같은 경험을 구현해 봅시다.

📂 준비물 (File Structure)
폴더 하나를 만들고 아래 파일들을 준비해주세요.

Plaintext
/search-roca-poc
  ├── kiosk.html      (키오스크 화면: 결과 표시 + QR 생성)
  ├── mobile.html     (모바일 화면: 나침반 + 길 안내)
  ├── arrow.png       (화살표 이미지: 구글에서 아무거나 다운로드)
  └── map_dummy.jpg   (매장 지도 이미지: 아무거나)
1. 키오스크 화면 (kiosk.html)
이 파일은 "Step 1의 결과물(JSON)"을 받아서 보여주는 역할을 합니다. 지금은 JSON을 코드 안에 박아넣습니다(Mocking).

기능: 상품 위치(target_x, y)를 URL 파라미터로 변환하여 QR코드로 굽습니다.

HTML
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Search-Roca Kiosk</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; }
        .result-box { border: 2px solid #ddd; padding: 20px; border-radius: 10px; display: inline-block; }
        #qrcode { margin-top: 20px; display: flex; justify-content: center; }
        h1 { color: #d63031; } /* 다이소 빨간색 */
    </style>
</head>
<body>

    <div class="result-box">
        <h1 id="product-name">상품명 로딩중...</h1>
        <p id="tts-text">안내 멘트 로딩중...</p>
        <hr>
        <h3>👇 스마트폰으로 스캔하여 길안내 받기</h3>
        <div id="qrcode"></div>
    </div>

    <script>
        // [Step 1 결과물] 가상 데이터 (LLM이 줬다고 가정)
        const mockData = {
            "product_name": "스텐 건지기 (채반)",
            "location_info": { "zone": "Kitchen_A", "x": 150, "y": 400 }, // 목표 좌표
            "tts_text": "2층 주방코너 A구역에 있습니다. QR을 찍어보세요."
        };

        // 1. 화면에 정보 뿌리기
        document.getElementById("product-name").innerText = mockData.product_name;
        document.getElementById("tts-text").innerText = mockData.tts_text;

        // 2. 모바일로 넘길 URL 생성 (핵심!)
        // ★중요★: 나중에 실제 호스팅 주소로 바꿔야 함 (지금은 로컬 테스트용)
        const mobileBaseUrl = window.location.href.replace("kiosk.html", "mobile.html");
        
        // 파라미터 인코딩: ?tx=150&ty=400&name=채반
        const finalUrl = `${mobileBaseUrl}?tx=${mockData.location_info.x}&ty=${mockData.location_info.y}&name=${encodeURIComponent(mockData.product_name)}`;

        console.log("Generated URL:", finalUrl);

        // 3. QR 코드 생성
        new QRCode(document.getElementById("qrcode"), {
            text: finalUrl,
            width: 200,
            height: 200
        });
    </script>
</body>
</html>


2. 모바일 화면 (mobile.html)
QR을 찍으면 열리는 페이지입니다. 나침반 센서를 이용해 화살표를 돌립니다.

기능: URL에서 좌표(tx, ty)를 읽고, 내 폰이 회전하는 만큼 화살표를 반대로 돌려 목표를 가리킵니다.

HTML:
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search-Roca Navi</title>
    <style>
        body { text-align: center; font-family: sans-serif; background-color: #f5f5f5; }
        #arrow-container { margin-top: 50px; position: relative; height: 300px; }
        #arrow { 
            width: 150px; 
            transition: transform 0.1s ease-out; /* 부드러운 회전 */
        }
        .status { margin-top: 20px; font-weight: bold; color: #333; }
        button { padding: 15px 30px; font-size: 18px; background: #d63031; color: white; border: none; border-radius: 5px; margin-top: 20px;}
    </style>
</head>
<body>

    <h2 id="target-name">목표지점</h2>
    <div class="status">폰을 들고 몸을 돌려보세요</div>

    <div id="arrow-container">
        <img id="arrow" src="arrow.png" alt="⬆️" style="transform: rotate(0deg);">
    </div>
    
    <p id="debug-info">센서 대기중...</p>

    <button onclick="requestPermission()">🧭 안내 시작하기</button>

    <script>
        // 1. URL 파라미터 읽기
        const params = new URLSearchParams(window.location.search);
        const targetX = parseInt(params.get('tx')) || 0;
        const targetY = parseInt(params.get('ty')) || 0;
        const targetName = params.get('name') || "목표";
        
        document.getElementById("target-name").innerText = targetName + " 찾는 중";

        // 내 위치 (일단 (0,0) 시작으로 가정)
        let myX = 0;
        let myY = 0;

        // 2. 나침반 로직
        function handleOrientation(event) {
            // alpha: 북쪽 기준 내 폰의 회전각 (0~360)
            // iOS와 Android의 alpha 기준이 다를 수 있음 (PoC에선 일단 진행)
            const alpha = event.alpha; 
            
            if (alpha === null) return;

            // 목표까지의 각도 계산 (아크탄젠트)
            // (y축이 아래로 증가하는 화면 좌표계 기준)
            const angleToTarget = Math.atan2(targetY - myY, targetX - myX) * (180 / Math.PI);
            
            // 최종 화살표 회전각 = 목표방향 - 내방향
            // (+90은 화살표 이미지 원본이 위를 향하고 있을 때 보정값)
            const rotation = angleToTarget - alpha - 90; 

            document.getElementById("arrow").style.transform = `rotate(${rotation}deg)`;
            document.getElementById("debug-info").innerText = `내 방향: ${Math.round(alpha)}° / 목표: ${Math.round(angleToTarget)}°`;
        }

        // 3. iOS 13+ 보안 권한 요청 (버튼 클릭 필수)
        function requestPermission() {
            if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                DeviceOrientationEvent.requestPermission()
                    .then(permissionState => {
                        if (permissionState === 'granted') {
                            window.addEventListener('deviceorientation', handleOrientation);
                            alert("센서 연결 성공!");
                        }
                    })
                    .catch(console.error);
            } else {
                // 안드로이드는 바로 실행
                window.addEventListener('deviceorientation', handleOrientation);
                alert("안내를 시작합니다.");
            }
        }
    </script>
</body>
</html>


🚀 실행 및 테스트 방법 (이게 제일 중요!)
이 코드를 그냥 file://로 열면 센서가 작동하지 않습니다. 반드시 HTTPS 환경이 필요합니다.

1. 로컬 서버 실행 (VS Code)
VS Code에서 Live Server 확장 프로그램을 설치하고, kiosk.html을 우클릭하여 Open with Live Server를 누르세요.

브라우저에 http://127.0.0.1:5500/kiosk.html 처럼 뜰 겁니다.

2. 외부 접속 허용 (Ngrok)
스마트폰이 내 PC의 로컬 서버에 접속하려면 터널링이 필요합니다. Ngrok을 설치하고 터미널에 입력하세요.

Bash:
ngrok http 5500

그러면 https://abcd-1234.ngrok-free.app 같은 주소가 나옵니다.


3. 최종 테스트 시나리오
PC: 브라우저 주소창에 Ngrok 주소 + /kiosk.html 입력.

(예: https://abcd-1234.ngrok-free.app/kiosk.html)

화면에 QR 코드가 뜹니다.

Mobile: 스마트폰 기본 카메라로 PC 화면의 QR을 스캔합니다.

Mobile Web: mobile.html로 이동합니다.

Action: 화면의 "안내 시작하기" 버튼을 누릅니다. (iOS 필수)

Check: 폰을 좌우로 돌려보세요. 화살표가 마치 나침반처럼 특정 방향(좌표상 목표)을 계속 가리키나요?


✅ Step 2 성공 판정 기준
키오스크의 QR을 찍었을 때, 모바일 URL에 ?name=스텐건지기 등이 잘 따라왔는가?

모바일에서 버튼을 눌렀을 때, debug-info 숫자가 폰을 돌릴 때마다 변하는가?

이것만 되면 "데이터 핸드오프 & 센서 연동" 기술 검증은 끝입니다. 지도 이미지를 넣거나 디자인을 입히는 건 그 다음입니다. 일단 화살표가 도는지부터 확인해 보세요!