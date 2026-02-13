import { useAppStore } from '../stores/useAppStore';
import FloorMap from '../components/FloorMap';
import MapQRCode from '../components/MapQRCode';
import Logo from '../components/Logo';

export default function MapScreen() {
  const selectedProduct = useAppStore((s) => s.selectedProduct);
  const mapInfo = useAppStore((s) => s.mapInfo);
  const reset = useAppStore((s) => s.reset);

  if (!mapInfo) return null;

  const counterNumber = selectedProduct?.counter_number ?? mapInfo.counter_number;
  const locationDesc = selectedProduct?.location_description ?? mapInfo.section_description;
  const floor = selectedProduct?.location_floor ?? mapInfo.floor;
  const qrUrl = typeof window !== 'undefined' ? window.location.href : '';

  // Format floor label
  const floorLabel = floor === 'B1' ? '지하1층' : floor === 'B2' ? '지하2층' : floor;

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <header className="px-8 pt-6 pb-2">
        <Logo />
      </header>

      {/* Title */}
      <h2 className="text-center text-2xl font-extrabold text-daiso-gray-900 mb-4">
        매장 지도
      </h2>

      {/* Main: map left + info right */}
      <main className="flex-1 flex items-start justify-center gap-10 px-8 pb-8 min-h-0">
        {/* Left: Map */}
        <div className="flex-1 h-full max-w-xl border border-gray-200 rounded-2xl overflow-hidden bg-gray-50">
          <FloorMap mapInfo={mapInfo} />
        </div>

        {/* Right: Location info + QR + button */}
        <div className="flex flex-col items-center gap-6 w-80 shrink-0 pt-4">
          {/* Location description */}
          <p className="text-xl font-bold text-daiso-gray-900 text-center leading-relaxed">
            <span className="text-daiso-red">📍</span>{' '}
            {counterNumber
              ? `${floorLabel} ${counterNumber}번 매대로 이동하세요`
              : `${floorLabel} ${locationDesc ?? ''}`
            }
          </p>

          {/* QR code */}
          <MapQRCode url={qrUrl} />

          {/* QR description */}
          <p className="text-sm text-pink-400 text-center leading-relaxed">
            QR코드를 스캔하면 스마트폰으로<br />
            지도를 보며 이동하실 수 있습니다
          </p>

          {/* Back button */}
          <button
            onClick={reset}
            className="flex items-center gap-3 px-8 py-4 rounded-2xl bg-gray-400 text-white
                       font-bold text-lg hover:bg-gray-500 active:scale-95 transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955a1.126 1.126 0 011.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
            다시 검색하기
          </button>
        </div>
      </main>
    </div>
  );
}
