"use client";

import { useState, useEffect } from "react";

export default function Home() {
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState("");

    useEffect(() => {
        setSessionId(Math.random().toString(36).substring(7));
    }, []);

    const handleSearch = async () => {
        if (!query) return;

        setLoading(true);
        // Add user message
        const newMessages = [...messages, { role: "User", content: query }];
        setMessages(newMessages);

        try {
            const res = await fetch("http://localhost:8000/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, session_id: sessionId }),
            });
            const data = await res.json();

            // Construct AI response
            let aiContent = "";
            if (data.needs_clarification && data.generated_question) {
                aiContent = `❓ ${data.generated_question}`;
            } else {
                aiContent = `✅ Intent: ${data.intent}\n📦 Found Slots: ${JSON.stringify(data.slots, null, 2)}`;
            }

            setMessages([...newMessages, { role: "AI", content: aiContent }]);
        } catch (error) {
            setMessages([...newMessages, { role: "AI", content: "Error communicating with server." }]);
        } finally {
            setLoading(false);
            setQuery("");
        }
    };

    return (
        <main className="flex min-h-screen flex-col items-center p-24 bg-gray-900 text-white">
            <h1 className="text-4xl font-bold mb-8 text-blue-400">Daiso AI Search</h1>

            <div className="w-full max-w-2xl bg-gray-800 rounded-lg p-4 h-[500px] overflow-y-auto mb-4 border border-gray-700">
                {messages.length === 0 && <p className="text-gray-500 text-center mt-40">무엇이든 물어보세요!</p>}
                {messages.map((msg, idx) => (
                    <div key={idx} className={`mb-4 p-3 rounded-lg ${msg.role === "User" ? "bg-blue-600 self-end ml-auto max-w-[80%]" : "bg-gray-700 self-start mr-auto max-w-[80%]"}`}>
                        <strong className="block text-xs text-gray-300 mb-1">{msg.role}</strong>
                        <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                    </div>
                ))}
            </div>

            <div className="flex w-full max-w-2xl gap-2">
                <input
                    type="text"
                    className="flex-1 p-3 rounded bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
                    placeholder="상품을 검색해보세요 (예: 파란색 볼펜)"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    disabled={loading}
                />
                <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="p-3 bg-blue-600 rounded hover:bg-blue-500 disabled:bg-gray-600 transition"
                >
                    {loading ? "..." : "검색"}
                </button>
            </div>
        </main>
    );
}
