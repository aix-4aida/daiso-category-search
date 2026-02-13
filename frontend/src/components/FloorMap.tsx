import { useRef, useState, useCallback } from 'react';
import type { MapInfo } from '../types';
import NavigationOverlay from './NavigationOverlay';

interface FloorMapProps {
  mapInfo: MapInfo;
}

export default function FloorMap({ mapInfo }: FloorMapProps) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  const handleImageLoad = useCallback(() => {
    if (imgRef.current) {
      setImgSize({
        width: imgRef.current.clientWidth,
        height: imgRef.current.clientHeight,
      });
    }
  }, []);

  return (
    <div className="relative w-full h-full">
      {/* Floor label */}
      <span className="absolute top-3 left-3 z-10 text-lg font-bold text-gray-700">
        {mapInfo.floor}
      </span>

      <img
        ref={imgRef}
        src={mapInfo.map_image}
        alt="매장 지도"
        className="w-full h-full object-contain"
        onLoad={handleImageLoad}
        onError={(e) => {
          (e.target as HTMLImageElement).src = '';
          (e.target as HTMLImageElement).alt = '지도를 불러올 수 없습니다';
        }}
      />

      {imgSize.width > 0 && mapInfo.waypoints && mapInfo.waypoints.length > 0 && mapInfo.destination && mapInfo.start && (
        <NavigationOverlay
          waypoints={mapInfo.waypoints}
          destination={mapInfo.destination}
          start={mapInfo.start}
          counterNumber={mapInfo.counter_number ?? null}
          width={imgSize.width}
          height={imgSize.height}
        />
      )}
    </div>
  );
}
