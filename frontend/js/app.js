/**
 * 어디다있소 - Main Application Logic (app.js)
 * Handles: tab navigation, carousel, voice recording, view transitions
 */

// ── State ──
let currentTab = 'home';
let currentSlide = 0;
let isRecording = false;
let carouselInterval = null;

// Backend API base URL (update for Lightsail)
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : window.location.origin;

// ── Tab Navigation ──
function switchTab(tab) {
    currentTab = tab;

    // Update tab bar
    document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
    const activeTab = document.querySelector(`.tab-item[data-tab="${tab}"]`);
    if (activeTab) activeTab.classList.add('active');

    // Show/hide views
    const views = ['home', 'loading', 'results', 'category'];
    views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) el.classList.toggle('hidden', v !== tab);
    });

    // Special actions per tab
    if (tab === 'category') {
        renderCategoryMap();
    }
}

// ── Carousel ──
function initCarousel() {
    const track = document.getElementById('carousel-track');
    if (!track) return;

    carouselInterval = setInterval(() => {
        const slides = track.querySelectorAll('.carousel-slide');
        currentSlide = (currentSlide + 1) % slides.length;
        updateCarousel();
    }, 5000);
}

function goToSlide(index) {
    currentSlide = index;
    updateCarousel();
}

function updateCarousel() {
    const track = document.getElementById('carousel-track');
    if (!track) return;
    track.style.transform = `translateX(-${currentSlide * 100}%)`;

    // Update dots
    document.querySelectorAll('.carousel-dots .dot').forEach((d, i) => {
        d.classList.toggle('active', i === currentSlide);
    });
}

// ── Voice Recording (Real Implementation) ──
let mediaRecorder = null;
let audioChunks = [];

async function toggleVoice() {
    const btn = document.getElementById('mic-btn');
    const label = document.querySelector('.voice-label');

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                label.textContent = '인식 중...';

                // Show loading immediately
                showLoading('음성 분석 중...');

                try {
                    const resultData = await searchProductsAudio(audioBlob);

                    if (resultData.status === 'success') {
                        document.getElementById('search-input').value = resultData.query;
                        showResults(resultData.query, resultData.results);
                        label.textContent = '인식 완료';
                    } else if (resultData.status === 'filtered') {
                        label.textContent = resultData.message;
                        switchViewRaw('home');
                        alert(resultData.message);
                    } else {
                        label.textContent = resultData.message || '다시 말씀해주세요.';
                        switchViewRaw('home');
                    }
                } catch (err) {
                    console.error('Voice Search Error:', err);
                    label.textContent = '오류가 발생했습니다.';
                    switchViewRaw('home');
                }
            };

            mediaRecorder.start();
            isRecording = true;
            btn.classList.add('recording');
            label.textContent = '듣고 있습니다...';

            // Auto stop after 5 seconds
            setTimeout(() => {
                if (isRecording) stopVoice();
            }, 5000);

        } catch (err) {
            console.error('Mic access error:', err);
            alert('마이크 접근 권한이 필요합니다.');
        }
    } else {
        stopVoice();
    }
}

function stopVoice() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    isRecording = false;
    const btn = document.getElementById('mic-btn');
    btn.classList.remove('recording');
}

// ── Search ──
function doSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) {
        alert('검색어를 입력해주세요.');
        return;
    }

    // Show loading
    showLoading(query);

    // Call backend API
    searchProducts(query).then(results => {
        showResults(query, results);
    });
}

// ── Loading View ──
function showLoading(query) {
    switchViewRaw('loading');
    document.getElementById('loading-query').textContent = query;

    // Animate progress
    let progress = 0;
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    const circumference = 2 * Math.PI * 90;

    fill.style.strokeDasharray = circumference;

    const interval = setInterval(() => {
        progress += Math.random() * 15 + 5;
        if (progress > 95) progress = 95;

        const offset = circumference - (progress / 100) * circumference;
        fill.style.strokeDashoffset = offset;
        text.textContent = `${Math.round(progress)}%`;

        if (progress >= 95) clearInterval(interval);
    }, 300);
}

// ── Results View ──
function showResults(query, results) {
    switchViewRaw('results');

    document.getElementById('results-count').textContent = `검색 결과 ${results.length}개`;

    const list = document.getElementById('results-list');
    list.innerHTML = '';

    results.forEach((r, i) => {
        const card = document.createElement('div');
        card.className = `result-card ${i === 0 ? 'selected' : ''}`;
        card.onclick = () => selectResult(i, r);
        card.innerHTML = `
      <div class="result-img" style="background:#FFEBEB;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#E50000;border-radius:12px;">${r.initial || '상'}</div>
      <div class="result-info">
        <h3>${i + 1}. ${r.name}</h3>
        <div class="result-location"><span style="color:#E50000;font-weight:600;">●</span> ${r.location}</div>
        <div class="result-price">${r.price}</div>
      </div>
    `;
        list.appendChild(card);
    });

    // Render map + QR with first result
    if (results.length > 0) {
        renderResultMap(results[0]);
        generateQR(results[0]);
    }
}

function selectResult(index, result) {
    document.querySelectorAll('.result-card').forEach((c, i) => {
        c.classList.toggle('selected', i === index);
    });
    renderResultMap(result);
    generateQR(result);
}

// ── QR Code Generation ──
function generateQR(result) {
    const qrArea = document.getElementById('qr-area');
    if (!qrArea) return;
    qrArea.innerHTML = '';

    const mobileUrl = `${window.location.origin}/mobile-map.html?name=${encodeURIComponent(result.name)}&shelf=${encodeURIComponent(result.location)}`;

    try {
        new QRCode(qrArea, {
            text: mobileUrl,
            width: 130,
            height: 130,
            colorDark: '#333333',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M
        });
    } catch (e) {
        qrArea.innerHTML = '<div style="width:130px;height:130px;background:#f5f5f5;border:2px dashed #ddd;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#999;">QR 코드</div>';
        console.warn('QRCode library not loaded:', e);
    }
}

// ── View Switching (raw, no tab update) ──
function switchViewRaw(view) {
    ['home', 'loading', 'results', 'category'].forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) el.classList.toggle('hidden', v !== view);
    });
}

// ── Help Dialog ──
function showHelp() {
    alert('어디다있소 도움말\n\n1. 마이크 버튼을 눌러 상품명을 말씀하세요.\n2. 또는 검색창에 직접 입력하세요.\n3. 검색 결과에서 매장 지도와 QR 코드를 확인하세요.\n4. QR 코드를 스캔하면 모바일에서 AR 네비게이션을 이용할 수 있습니다.');
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    initCarousel();
    renderCategoryMap();
});
