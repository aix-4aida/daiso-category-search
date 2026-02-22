/**
 * search.js
 * Result rendering and product card interactions.
 */

function renderResults(products, query) {
    const list = document.getElementById('results-list');
    const countLabel = document.getElementById('results-count');

    list.innerHTML = '';
    countLabel.innerText = `${query} 검색 결과 ${products.length}개`;

    if (products.length === 0) {
        list.innerHTML = '<div class="no-results">검색 결과가 없습니다.</div>';
        return;
    }

    products.forEach((p, index) => {
        const card = document.createElement('div');

        // Best Pick Logic (First Item)
        if (index === 0) {
            card.className = 'best-pick-card selected';
            card.innerHTML = `<div class="best-pick-badge">BEST PICK</div>`;
        } else {
            card.className = 'result-card';
        }

        const price = p.formatted_price || (p.price ? p.price.toLocaleString() + '원' : '가격 정보 없음');
        const category = p.meta?.category_middle || p.meta?.category_major || '일반';
        const floor = p.location?.floor || 'B1';
        const section = p.location?.section || 'N01';
        const shelfLabel = p.location?.shelf_label || '일반매대';

        const imgHTML = p.image_url
            ? `<img src="${p.image_url}" class="result-img-real" onerror="this.src='https://placehold.co/100x100?text=No+Image'">`
            : `<div class="result-img-text">${floor}</div>`;

        // Append content (similar structure but Best Pick has different CSS layout)
        card.innerHTML += `
            <div class="result-img">${imgHTML}</div>
            <div class="result-info">
                ${index !== 0 ? `<div class="card-tag">${category}</div>` : ''}
                <h3 class="result-title">${p.name}</h3>
                <div class="result-location">위치: <strong>${floor}-${section}</strong> (${shelfLabel})</div>
                <div class="result-price">${price}</div>
            </div>
            ${index !== 0 ? `
            <div class="card-arrow">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 18l6-6-6-6" />
                </svg>
            </div>` : ''}
        `;

        // Click event
        card.onclick = () => selectResult(p, card);
        list.appendChild(card);

        // Render first result map by default
        if (index === 0) {
            selectResult(p, card);
        }
    });
}

function selectResult(product, cardElement) {
    // UI Update
    document.querySelectorAll('.result-card, .best-pick-card').forEach(c => c.classList.remove('selected'));
    cardElement.classList.add('selected');

    // Render Map (defined in map.js)
    if (typeof renderResultMap === 'function') {
        renderResultMap(product);
    }

    // Generate QR
    generateQR(product);
}

function generateQR(product) {
    const qrArea = document.getElementById('qr-area');
    qrArea.innerHTML = ''; // Clear existing

    // Using qrcodejs (loaded in index.html)
    // Generate QR code for mobile transplant
    const floor = product.location?.floor || 'B1';
    const section = product.location?.section || 'N01';
    const shelfParam = `${floor}-${section}`;

    // Use window.location.origin to support local, tunnel, or production environments
    const nameParam = product.name ? product.name.substring(0, 15) : '';
    const mobileUrl = `${window.location.origin}/mobile-ar.html?shelf=${encodeURIComponent(shelfParam)}&name=${encodeURIComponent(nameParam)}`;

    new QRCode(qrArea, {
        text: mobileUrl,
        width: 140,
        height: 140,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M
    });
}
