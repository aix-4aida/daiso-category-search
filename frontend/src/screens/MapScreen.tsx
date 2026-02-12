import { useAppStore } from '../stores/useAppStore';
import FloorMap from '../components/FloorMap';

export default function MapScreen() {
  const selectedProduct = useAppStore((s) => s.selectedProduct);
  const mapInfo = useAppStore((s) => s.mapInfo);
  const setScreen = useAppStore((s) => s.setScreen);
  const reset = useAppStore((s) => s.reset);

  if (!mapInfo) return null;

  return (
    <div className="flex flex-col items-center min-h-screen bg-daiso-gray-50 px-6 py-10">
      <h2 className="text-2xl font-bold text-daiso-gray-900 mb-6">
        매장 위치 안내
      </h2>

      <FloorMap mapInfo={mapInfo} product={selectedProduct} />

      <div className="flex gap-4 mt-8">
        <button
          onClick={() => setScreen('results')}
          className="px-6 py-3 rounded-full bg-daiso-gray-200 text-daiso-gray-700
                     font-bold hover:bg-daiso-gray-500 hover:text-white
                     active:scale-95 transition-all"
        >
          결과로 돌아가기
        </button>
        <button
          onClick={reset}
          className="px-6 py-3 rounded-full bg-daiso-red text-white
                     font-bold hover:bg-daiso-red-dark
                     active:scale-95 transition-all"
        >
          다시 검색하기
        </button>
      </div>
    </div>
  );
}
