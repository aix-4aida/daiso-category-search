/**
 * app.js
 * Main application logic, Speech API integration, and Navigation.
 */

let recognition;
let isListening = false;

document.addEventListener('DOMContentLoaded', () => {
    initSpeech();
    initCarousel();

    if (window.location.pathname.includes('results.html')) {
        executeSearchOnResultsPage();
    }
});

// --- 1. View Management (Multi-Page Routing) ---
function showView(viewId) {
    console.warn("showView is deprecated in multi-page architecture. Use location.href instead.");
}

function switchTab(tab) {
    if (tab === 'home') window.location.href = 'index.html';
    if (tab === 'category') window.location.href = 'map.html';
    if (tab === 'location') window.location.href = 'location.html';
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
    // Update center label if exists
    const label = document.querySelector('.voice-label');
    if (label) label.innerText = text;

    // Update top search bar simultaneously
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = text;
}

// --- 3. Search Execution ---
async function doSearch(query) {
    const text = query || (document.getElementById('search-input') ? document.getElementById('search-input').value : '');
    if (!text.trim()) return;

    // Redirect to results.html with query parameter
    window.location.href = `results.html?q=${encodeURIComponent(text)}`;
}

// Function to actually fetch and render results on results.html
async function executeSearchOnResultsPage() {
    const params = new URLSearchParams(window.location.search);
    const text = params.get('q');
    if (!text) return;

    document.getElementById('search-input').value = text;

    // Show Loading View
    document.getElementById('view-results').classList.add('hidden');
    const loadingView = document.getElementById('view-loading');
    if (loadingView) {
        loadingView.classList.remove('hidden');
        document.getElementById('loading-query').innerText = `'${text}'`;
        simulateProgress();
    }

    try {
        const response = await fetch('/api/search/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        });

        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();

        // Hide loading, Show results
        if (loadingView) loadingView.classList.add('hidden');
        document.getElementById('view-results').classList.remove('hidden');

        // Render results (defined in search.js)
        if (typeof renderResults === 'function') {
            renderResults(data.products || [], text);
        }

    } catch (error) {
        console.error('Search error:', error);
        alert('검색 중 오류가 발생했습니다.');
        window.location.href = 'index.html';
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
// --- 4. UI Helpers ---
function initCarousel() {
    const track = document.getElementById('carousel-track');
    const dots = document.querySelectorAll('.carousel-dots .dot');

    // Only initialize if carousel exists on the page
    if (!track || dots.length === 0) return;

    let currentSlide = 0;

    window.goToSlide = (index) => {
        currentSlide = index;
        track.style.transform = `translateX(-${index * 100}%)`;
        dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
    };

    // Auto slide
    setInterval(() => {
        currentSlide = (currentSlide + 1) % dots.length;
        window.goToSlide(currentSlide);
    }, 5000);
}

function showHelp() {
    alert('목소리나 텍스트로 상품을 검색해 보세요.\n검색 결과에서 상품을 누르면 위치를 안내해 드립니다.');
}
