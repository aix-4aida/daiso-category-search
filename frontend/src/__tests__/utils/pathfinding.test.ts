import { describe, it, expect } from 'vitest';
import { buildWaypoints, KIOSK_POSITION } from '../../utils/pathfinding';

describe('pathfinding', () => {
  it('should export KIOSK_POSITION at top center (B1 entrance)', () => {
    expect(KIOSK_POSITION.x).toBe(0.45);
    expect(KIOSK_POSITION.y).toBeLessThan(0.2);
  });

  it('should build waypoints from kiosk to destination below aisle', () => {
    const path = buildWaypoints(0.82, 0.48);
    expect(path.length).toBe(4);
    expect(path[0].x).toBe(KIOSK_POSITION.x);
    expect(path[0].y).toBe(KIOSK_POSITION.y);
    expect(path[path.length - 1].x).toBe(0.82);
    expect(path[path.length - 1].y).toBe(0.48);
  });

  it('should build shorter path for destination above aisle', () => {
    const path = buildWaypoints(0.30, 0.08);
    expect(path.length).toBe(3);
    expect(path[0].x).toBe(KIOSK_POSITION.x);
    expect(path[path.length - 1].x).toBe(0.30);
    expect(path[path.length - 1].y).toBe(0.08);
  });

  it('should have all coordinates normalized 0~1', () => {
    const path = buildWaypoints(0.82, 0.72);
    for (const p of path) {
      expect(p.x).toBeGreaterThanOrEqual(0);
      expect(p.x).toBeLessThanOrEqual(1);
      expect(p.y).toBeGreaterThanOrEqual(0);
      expect(p.y).toBeLessThanOrEqual(1);
    }
  });
});
