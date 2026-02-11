/**
 * 어디다있소 - Search Logic (search.js)
 * Connects to Backend API (/search/text)
 */

// Backend API base URL
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : window.location.origin;

/**
 * Helper: Generate UI metadata from backend result if missing
 */
function enrichResult(item) {
    const meta = item.meta || {};

    // 1. Initial (Category Icon)
    let initial = '상';
    const catMap = {
        '주방': '주', '욕실': '욕', '문구': '문', '뷰티': '뷰',
        '식품': '식', '청소': '청', '수납': '수', '캠핑': '캠', '스포츠': '스'
    };
    if (meta.major && catMap[meta.major]) initial = catMap[meta.major];
    else if (item.name) initial = item.name.charAt(0);

    // 2. Location & Floor Mapping
    let location = 'B1-C01'; // Default
    let floor = 'B1';

    // Image-based Map IDs (Matching map.js)
    if (meta.major === '주방') { location = 'B2-KI01'; floor = 'B2'; }
    else if (meta.major === '식품') { location = 'B1-K01'; floor = 'B1'; }
    else if (meta.major === '청소' || meta.major === '욕실') { location = 'B2-BA01'; floor = 'B2'; }
    else if (meta.major === '문구') { location = 'B1-A01'; floor = 'B1'; }
    else if (meta.major === '수납정리') { location = 'B2-ST01'; floor = 'B2'; }
    else if (meta.major === '스포츠' || meta.major === '애견') { location = 'B2-SP01'; floor = 'B2'; }
    else if (meta.major === '화장품' || meta.major === '뷰티') { location = 'B1-C01'; floor = 'B1'; }

    const price = item.price || '3,000원';

    return {
        name: item.name,
        id: location.includes('-') ? location.split('-')[1] : location,
        location: location,
        floor: floor,
        section: meta.major || '기타',
        price: price,
        initial: initial,
        score: item.score || 0
    };
}

/**
 * Search products via Backend API
 */
async function searchProducts(query) {
    if (!query) return [];

    try {
        const response = await fetch(`${API_BASE_URL}/search/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Combine 'result' (Reranked Top 1) and 'candidates'
            const bestMatch = data.result;
            const candidates = data.candidates || [];

            // Deduplicate: remove bestMatch from candidates if present
            const uniqueCandidates = candidates.filter(c => c.id !== bestMatch.id);

            // Format Best Match
            const formattedBest = {
                name: bestMatch.product,
                location: `${bestMatch.location.floor}-${bestMatch.location.id}`, // e.g. B1-Unknown
                floor: bestMatch.location.floor,
                section: bestMatch.location.section,
                price: bestMatch.price || '3,000원',
                initial: bestMatch.initial || bestMatch.product.charAt(0)
            };

            // Fix location if it's "Unknown" or "위치정보없음"
            if (formattedBest.location.includes('Unknown')) {
                const enriched = enrichResult({ name: bestMatch.product, meta: bestMatch.meta });
                formattedBest.location = enriched.location;
                formattedBest.floor = enriched.floor;
                formattedBest.initial = enriched.initial;
            }

            // Format Candidates
            const formattedCandidates = uniqueCandidates.map(enrichResult);

            // Return combined list (Top 1 + Top 4 candidates)
            return [formattedBest, ...formattedCandidates].slice(0, 5);
        }

        return [];
    } catch (e) {
        console.error('Search API error:', e);
        // Fallback: Return empty or use a tiny offline fallback
        return [];
    }
}
/**
 * Search products via Backend API (Audio)
 */
async function searchProductsAudio(audioBlob) {
    if (!audioBlob) return { status: 'error', message: 'No audio provided' };

    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        const response = await fetch(`${API_BASE_URL}/search/audio`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            const bestMatch = data.result;
            const candidates = data.candidates || [];
            const uniqueCandidates = candidates.filter(c => c.id !== bestMatch.id);

            const formattedBest = {
                name: bestMatch.product,
                location: `${bestMatch.location.floor}-${bestMatch.location.id}`,
                floor: bestMatch.location.floor,
                section: bestMatch.location.section,
                price: bestMatch.price || '3,000원',
                initial: bestMatch.initial || bestMatch.product.charAt(0)
            };

            if (formattedBest.location.includes('Unknown')) {
                const enriched = enrichResult({ name: bestMatch.product, meta: bestMatch.meta });
                formattedBest.location = enriched.location;
                formattedBest.floor = enriched.floor;
                formattedBest.initial = enriched.initial;
            }

            const formattedCandidates = uniqueCandidates.map(enrichResult);
            return {
                status: 'success',
                query: data.query,
                results: [formattedBest, ...formattedCandidates].slice(0, 5)
            };
        }

        return {
            status: data.status || 'error',
            message: data.message || '인식 실패',
            query: data.query || ''
        };
    } catch (e) {
        console.error('Audio Search API error:', e);
        return { status: 'error', message: '서버 연결 오류가 발생했습니다.' };
    }
}
