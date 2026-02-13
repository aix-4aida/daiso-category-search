import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import MapQRCode from '../../components/MapQRCode';

describe('MapQRCode', () => {
  it('should render QR code SVG', () => {
    const { container } = render(<MapQRCode url="https://example.com/map" />);
    const svg = container.querySelector('svg');
    expect(svg).toBeTruthy();
  });

  it('should not render when url is empty', () => {
    const { container } = render(<MapQRCode url="" />);
    const svg = container.querySelector('svg');
    expect(svg).toBeFalsy();
  });
});
