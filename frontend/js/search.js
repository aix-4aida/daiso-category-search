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
    // Map backend meta to frontend expected fields
    const meta = item.meta || {};

    // 1. Initial (Category Icon)
    // Use major category first char, or first char of name
    let initial = '상';
    if (meta.major) initial = meta.major.charAt(0);
    else if (item.name) initial = item.name.charAt(0);

    // Map specific categories to known initials
    const catMap = {
        '주방': '주', '욕실': '욕', '문구': '문', '뷰티': '뷰',
        '식품': '식', '청소': '청', '수납': '수', '캠핑': '캠'
    };
    if (meta.major && catMap[meta.major]) initial = catMap[meta.major];

    // 2. Location & Floor
    // Backend returns meta: { major, middle } usually
    // We need 'B1-A01' format. 
    // Mock mapping for demo if real location missing
    let location = 'B1-A01';
    let floor = 'B1';

    if (meta.major === '주방' || meta.major === '식품') { location = 'B2-K01'; floor = 'B2'; }
    else if (meta.major === '청소' || meta.major === '욕실') { location = 'B2-CL01'; floor = 'B2'; }
    else if (meta.major === '문구') { location = 'B2-A02'; floor = 'B2'; }
    else if (meta.major === '화장품' || meta.major === '뷰티') { location = 'B1-C01'; floor = 'B1'; }

    // 3. Price (Mock for now)
    const price = item.price || '3,000원'; // Default mock price

    return {
        name: item.name,
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
