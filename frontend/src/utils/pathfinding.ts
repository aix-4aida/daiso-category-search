export interface Point {
  x: number;
  y: number;
}

// Kiosk at B1 entrance (top center)
export const KIOSK_POSITION: Point = { x: 0.45, y: 0.05 };

const MAIN_AISLE_Y = 0.15;

/**
 * Build navigation waypoints from kiosk to destination.
 * Route: kiosk → main aisle → horizontal move → destination
 * For destinations above the aisle, takes a shorter direct path.
 */
export function buildWaypoints(destX: number, destY: number): Point[] {
  const kx = KIOSK_POSITION.x;
  const ky = KIOSK_POSITION.y;

  if (destY <= MAIN_AISLE_Y) {
    return [
      { x: kx, y: ky },
      { x: destX, y: ky },
      { x: destX, y: destY },
    ];
  }

  return [
    { x: kx, y: ky },
    { x: kx, y: MAIN_AISLE_Y },
    { x: destX, y: MAIN_AISLE_Y },
    { x: destX, y: destY },
  ];
}
