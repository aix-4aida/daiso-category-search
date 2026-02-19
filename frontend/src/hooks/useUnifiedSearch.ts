import { useState } from 'react';
import { useRouter } from 'next/navigation';

export interface SearchResult {
    status: 'ok' | 'no_result' | 'need_clarify' | 'not_supported' | 'error';
    results?: any[];
    message?: string;
    suggestions?: string[];
    keyword?: string;
    reranked?: any[];
}

export const useUnifiedSearch = () => {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (query: string, inputMode: 'text' | 'voice' = 'text') => {
        if (!query.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    input_mode: inputMode,
                    session_id: `session_${Date.now()}`
                }),
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.status}`);
            }

            const data: SearchResult = await response.json();

            // Handle different statuses
            if (data.status === 'ok') {
                // Store results in localStorage to pass to Result page (legacy pattern)
                // We use the same keys as VoiceSearch to reuse VoiceResults page
                if (data.keyword) localStorage.setItem('voiceSearchKeyword', data.keyword);
                if (data.results) localStorage.setItem('voiceSearchResults', JSON.stringify(data.results));
                if (data.reranked) localStorage.setItem('voiceRerankedResults', JSON.stringify(data.reranked));

                // Navigate to Results
                router.push(`/VoiceResults?q=${encodeURIComponent(data.keyword || query)}`);
            } else if (data.status === 'need_clarify' || data.status === 'not_supported' || data.status === 'no_result') {
                // For clarification/no_result, we might want to show a specific UI.
                // For now, let's go to VoiceResults but pass a flag or handle it there?
                // Or maybe route to a new 'Clarify' page?
                // The requirements say: "suggestions... 3-1 failure branch".
                // VoiceResults page currently handles "No Result" case simple.

                // Let's store the full response to let the page handle it
                localStorage.setItem('searchResponse', JSON.stringify(data));

                // We can reuse VoiceResults but maybe add a query param to indicate status
                router.push(`/VoiceResults?q=${encodeURIComponent(query)}&status=${data.status}`);
            } else {
                setError(data.message || "Unknown error");
            }

        } catch (err: any) {
            console.error("Search error:", err);
            setError(err.message || "Something went wrong");
        } finally {
            setIsLoading(false);
        }
    };

    return {
        handleSearch,
        isLoading,
        error
    };
};
