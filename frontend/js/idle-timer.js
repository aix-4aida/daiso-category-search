/**
 * Idle Timer
 * Resets the application to the Home screen after 30 seconds of inactivity.
 */

(function () {
    const IDLE_TIMEOUT = 30000; // 30 seconds
    let idleTimer;

    function resetTimer() {
        clearTimeout(idleTimer);
        idleTimer = setTimeout(goHome, IDLE_TIMEOUT);
    }

    function goHome() {
        // Only redirect if not already on search home and not playing TTS/Mic
        // We can check the active view or just reload/reset state.
        // For Kiosk mode, full reset is often safer.

        // Ensure we are not interrupting active interaction (though 30s implies no interaction)
        console.log("Idle timeout reached. Returning to Home.");

        // Using existing transition function if available, or manual handling
        if (typeof showView === 'function') {
            showView('view-home');
        } else {
            // Fallback
            window.location.href = 'index.html';
        }

        // Reset any search state if needed
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
    }

    // Events to detect activity
    const activityEvents = [
        'mousedown', 'mousemove', 'keydown',
        'scroll', 'touchstart', 'click'
    ];

    activityEvents.forEach(evt => {
        document.addEventListener(evt, resetTimer, true);
    });

    // Initialize
    resetTimer();
})();
