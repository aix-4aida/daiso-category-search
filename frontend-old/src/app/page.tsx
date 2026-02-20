import Link from 'next/link';

export default function Home() {
    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
            <h1 className="text-5xl font-bold mb-8 text-blue-400">Daiso AI Search</h1>
            <p className="text-xl mb-12 text-gray-300">다이소 상품 찾기 AI 키오스크</p>

            <Link href="/kioskmode">
                <button className="px-8 py-4 bg-blue-600 rounded-lg text-2xl font-bold hover:bg-blue-500 transition shadow-lg hover:scale-105 transform duration-200">
                    Kiosk Mode 시작하기
                </button>
            </Link>
        </main>
    );
}
