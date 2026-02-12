import { useAppStore } from '../stores/useAppStore';
import SearchBar from '../components/SearchBar';
import MicButton from '../components/MicButton';
import CategoryChips from '../components/CategoryChips';

export default function HomeScreen() {
  const search = useAppStore((s) => s.search);
  const error = useAppStore((s) => s.error);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-daiso-gray-50 px-6">
      <div className="flex flex-col items-center gap-8 -mt-16">
        {/* Logo / Title */}
        <div className="text-center">
          <h1 className="text-5xl font-extrabold text-daiso-red mb-2">
            어디다있소
          </h1>
          <p className="text-lg text-daiso-gray-500">
            다이소 상품 위치를 찾아드립니다
          </p>
        </div>

        {/* Search */}
        <SearchBar onSearch={search} />

        {/* Mic */}
        <div className="flex flex-col items-center gap-3">
          <MicButton />
          <p className="text-sm text-daiso-gray-500">
            마이크를 눌러 음성으로 검색하세요
          </p>
        </div>

        {/* Error */}
        {error && (
          <p className="text-daiso-red font-medium" role="alert">
            {error}
          </p>
        )}

        {/* Popular categories */}
        <div className="mt-4">
          <p className="text-center text-sm text-daiso-gray-500 mb-3">
            인기 검색
          </p>
          <CategoryChips onSelect={search} />
        </div>
      </div>
    </div>
  );
}
