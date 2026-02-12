import type { MapInfo, Product } from '../types';

interface FloorMapProps {
  mapInfo: MapInfo;
  product: Product | null;
}

export default function FloorMap({ mapInfo, product }: FloorMapProps) {
  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative rounded-2xl overflow-hidden shadow-lg bg-white">
        <img
          src={mapInfo.map_image}
          alt="매장 지도"
          className="w-full h-auto"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '';
            (e.target as HTMLImageElement).alt = '지도를 불러올 수 없습니다';
          }}
        />
        {product && (
          <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur
                          rounded-xl p-4 shadow-lg">
            <p className="text-sm text-daiso-gray-500">{mapInfo.section} 코너</p>
            <p className="text-lg font-bold text-daiso-gray-900">{product.name}</p>
            <p className="text-sm text-daiso-red font-bold">
              {product.price.toLocaleString()}원
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
