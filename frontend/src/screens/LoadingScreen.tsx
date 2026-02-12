import { useAppStore } from '../stores/useAppStore';

export default function LoadingScreen() {
  const query = useAppStore((s) => s.query);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-daiso-gray-50">
      <div className="flex flex-col items-center gap-8">
        {/* Spinner */}
        <div className="relative w-24 h-24">
          <div className="absolute inset-0 rounded-full border-4 border-daiso-gray-200" />
          <div className="absolute inset-0 rounded-full border-4 border-daiso-red border-t-transparent animate-spin" />
        </div>

        <div className="text-center">
          <p className="text-xl font-bold text-daiso-gray-900 mb-2">
            매장 내 상품 위치를 찾고 있습니다...
          </p>
          {query && (
            <p className="text-daiso-gray-500">
              &ldquo;{query}&rdquo;
            </p>
          )}
          <p className="text-sm text-daiso-gray-500 mt-4">
            잠시만 기다려주세요
          </p>
        </div>
      </div>
    </div>
  );
}
