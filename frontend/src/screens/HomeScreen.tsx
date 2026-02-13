import { useAppStore } from '../stores/useAppStore';
import SearchBar from '../components/SearchBar';
import MicButton from '../components/MicButton';
import Logo from '../components/Logo';
import BottomNav from '../components/BottomNav';

function ErrorView({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="px-8 pt-6">
        <Logo />
      </header>

      <main className="flex-1 flex flex-col items-center justify-center -mt-10 px-8">
        <h2 className="text-4xl font-extrabold text-daiso-gray-900 mb-4">
          죄송합니다
        </h2>
        <p className="text-xl text-gray-400 mb-10">
          해당 상품의 위치를 찾을 수 없습니다
        </p>

        {/* Suggestions */}
        <div className="bg-gray-50 rounded-2xl p-8 w-full max-w-lg mb-10">
          <p className="font-bold text-daiso-gray-900 mb-4">
            💡 이렇게 검색해 보세요 :
          </p>
          <p className="text-gray-400 mb-2">&ldquo;세탁세제&rdquo;</p>
          <p className="text-gray-400 mb-2">&ldquo;주방세제&rdquo;</p>
          <p className="text-gray-400">&ldquo;청소포 위치 알려줘&rdquo;</p>
        </div>

        {/* Action buttons */}
        <div className="flex gap-4">
          <button
            onClick={onReset}
            className="flex items-center gap-3 px-8 py-5 rounded-2xl bg-gray-400 text-white
                       font-bold text-lg hover:bg-gray-500 active:scale-95 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955a1.126 1.126 0 011.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
            다시 검색하기
          </button>
          <button
            className="flex items-center gap-3 px-8 py-5 rounded-2xl bg-white border border-gray-200 text-gray-600
                       font-bold text-lg hover:bg-gray-50 active:scale-95 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-6 h-6 text-daiso-red">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
            </svg>
            도움말
          </button>
        </div>
      </main>
    </div>
  );
}

export default function HomeScreen() {
  const search = useAppStore((s) => s.search);
  const error = useAppStore((s) => s.error);
  const reset = useAppStore((s) => s.reset);

  // Show error view
  if (error) {
    return <ErrorView onReset={reset} />;
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header: Logo + Search bar */}
      <header className="flex items-center gap-4 px-8 pt-6 pb-4">
        <Logo />
        <div className="flex items-center gap-3 flex-1">
          <MicButton />
          <SearchBar onSearch={search} />
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center px-8 overflow-hidden">
        {/* Banner */}
        <div className="w-full max-w-4xl rounded-2xl overflow-hidden">
          <img
            src="/banner01.png"
            alt="설연휴 쇼핑도 다이소에서"
            className="w-full h-auto object-cover"
          />
        </div>
      </main>

      {/* Bottom navigation */}
      <BottomNav />
    </div>
  );
}
