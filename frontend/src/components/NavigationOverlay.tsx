import type { Waypoint } from '../types';

interface NavigationOverlayProps {
  waypoints: Waypoint[];
  destination: Waypoint;
  start: Waypoint;
  counterNumber: number | null;
  width: number;
  height: number;
}

export default function NavigationOverlay({
  waypoints,
  destination,
  start,
  counterNumber,
  width,
  height,
}: NavigationOverlayProps) {
  if (waypoints.length === 0) return <svg />;

  const toPixel = (p: Waypoint) => ({
    x: p.x * width,
    y: p.y * height,
  });

  const points = waypoints.map(toPixel);
  const pointsStr = points.map(p => `${p.x},${p.y}`).join(' ');

  const dest = toPixel(destination);
  const startPx = toPixel(start);

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
    >
      {/* Dotted path line */}
      <polyline
        points={pointsStr}
        fill="none"
        stroke="#E31836"
        strokeWidth={3}
        strokeDasharray="10 6"
        strokeLinecap="round"
      />

      {/* Start marker */}
      <circle cx={startPx.x} cy={startPx.y} r={8} fill="#3B82F6" />
      <text
        x={startPx.x}
        y={startPx.y - 14}
        textAnchor="middle"
        fontSize={12}
        fontWeight="bold"
        fill="#3B82F6"
      >
        현위치
      </text>

      {/* Destination marker */}
      <circle cx={dest.x} cy={dest.y} r={10} fill="#E31836" />
      <circle cx={dest.x} cy={dest.y} r={5} fill="white" />
      {counterNumber && (
        <text
          x={dest.x}
          y={dest.y - 16}
          textAnchor="middle"
          fontSize={13}
          fontWeight="bold"
          fill="#E31836"
        >
          {counterNumber}번 매대
        </text>
      )}
    </svg>
  );
}
