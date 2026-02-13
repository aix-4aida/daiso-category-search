import { useAppStore } from '../stores/useAppStore';
import Logo from '../components/Logo';

export default function LoadingScreen() {
  const query = useAppStore((s) => s.query);

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Logo */}
      <header className="px-8 pt-6">
        <Logo />
      </header>

      {/* Content */}
      <main className="flex-1 flex flex-col items-center justify-center -mt-16">
        <h2 className="text-4xl font-extrabold text-daiso-gray-900 mb-10">
          찾는 중입니다...
        </h2>

        {/* Red dot circle spinner */}
        <div className="w-32 h-32 mb-10 animate-spin" style={{ animationDuration: '1.2s' }}>
          <div className="relative w-full h-full">
            {Array.from({ length: 12 }).map((_, i) => {
              const angle = (i * 30 * Math.PI) / 180;
              const x = 50 + 40 * Math.cos(angle - Math.PI / 2);
              const y = 50 + 40 * Math.sin(angle - Math.PI / 2);
              const opacity = i <= 6 ? 1 - i * 0.13 : 0.15;
              return (
                <div
                  key={i}
                  className="absolute w-3.5 h-3.5 rounded-full"
                  style={{
                    left: `${x}%`,
                    top: `${y}%`,
                    transform: 'translate(-50%, -50%)',
                    backgroundColor: `rgba(230, 0, 18, ${opacity})`,
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Query pill */}
        {query && (
          <div className="bg-gray-100 rounded-full px-8 py-3 mb-8">
            <p className="text-lg text-gray-400 font-medium">
              &ldquo;{query}&rdquo;
            </p>
          </div>
        )}

        <p className="text-2xl font-bold text-daiso-gray-900">
          잠시만 기다려주세요
        </p>
      </main>
    </div>
  );
}
