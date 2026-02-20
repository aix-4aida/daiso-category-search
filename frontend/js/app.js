/**
 * app.js
 * Main application logic, Speech API integration, and Navigation.
 */

// API Base URL: auto-detect local vs deployed
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : '/api';

let recognition;
let isListening = false;

document.addEventListener('DOMContentLoaded', () => {
    initSpeech();
    initCarousel();
});

// --- 1. View Management ---
function showView(viewId) {
    const views = ['view-home', 'view-loading', 'view-results', 'view-category'];
    views.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });

    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove('hidden');
        if (viewId === 'view-results') {
            target.classList.add('results-page');
        }
    }

    // Tab bar active state
    document.querySelectorAll('.tab-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === (viewId.split('-')[1] || 'home'));
    });
}

function switchTab(tab) {
    if (tab === 'home') showView('view-home');
    if (tab === 'category') showView('view-category');
}

// --- 2. Speech API ---
function initSpeech() {
    if (!('webkitSpeechRecognition' in window)) {
        console.warn('Web Speech API is not supported in this browser.');
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'ko-KR';

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('mic-btn').classList.add('active');
        updateVoiceLabel('듣고 있어요...');
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        if (finalTranscript) {
            updateVoiceLabel(finalTranscript);
            setTimeout(() => doSearch(finalTranscript), 500);
        } else if (interimTranscript) {
            updateVoiceLabel(interimTranscript);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopVoice();
    };

    recognition.onend = () => {
        stopVoice();
    };
}

function toggleVoice() {
    if (isListening) {
        stopVoice();
    } else {
        startVoice();
    }
}

function startVoice() {
    if (recognition) {
        recognition.start();
    }
}

function stopVoice() {
    if (recognition) {
        recognition.stop();
    }
    isListening = false;
    document.getElementById('mic-btn').classList.remove('active');
    updateVoiceLabel('어떤 상품의 위치를 알고 싶으세요?');
}

function updateVoiceLabel(text) {
    const label = document.querySelector('.voice-label');
    if (label) label.innerText = text;
}

// --- 3. Search Execution ---
async function doSearch(query) {
    const text = query || document.getElementById('search-input').value;
    if (!text.trim()) return;

    // Loading state
    showView('view-loading');
    document.getElementById('loading-query').innerText = `'${text}'`;
    simulateProgress();

    try {
        const response = await fetch(`${API_BASE}/search/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        });

        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();

        // Render results (defined in search.js)
        if (typeof renderResults === 'function') {
            renderResults(data.products || [], text);
        }

        showView('view-results');
    } catch (error) {
        console.error('Search error:', error);
        alert('검색 중 오류가 발생했습니다.');
        showView('view-home');
    }
}

function simulateProgress() {
    let progress = 0;
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');

    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        if (fill) fill.style.strokeDashoffset = 565 - (565 * progress) / 100;
        if (text) text.innerText = `${Math.floor(progress)}%`;
    }, 200);
}

// --- 4. UI Helpers ---
function initCarousel() {
    let currentSlide = 0;
    const track = document.getElementById('carousel-track');
    const dots = document.querySelectorAll('.carousel-dots .dot');

    window.goToSlide = (index) => {
        currentSlide = index;
        if (track) track.style.transform = `translateX(-${index * 100}%)`;
        dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
    };

    // Auto slide
    setInterval(() => {
        currentSlide = (currentSlide + 1) % dots.length;
        goToSlide(currentSlide);
    }, 5000);
}

function showHelp() {
    alert('목소리나 텍스트로 상품을 검색해 보세요.\n검색 결과에서 상품을 누르면 위치를 안내해 드립니다.');
}
