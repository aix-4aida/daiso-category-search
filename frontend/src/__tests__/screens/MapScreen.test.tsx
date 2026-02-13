import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MapScreen from '../../screens/MapScreen';
import { useAppStore } from '../../stores/useAppStore';

beforeEach(() => {
  useAppStore.setState({
    screen: 'map',
    mapInfo: {
      floor: 'B1',
      section: '뷰티/위생',
      map_image: '/maps/map_b1.jpg',
      counter_number: 7,
      section_description: '화장품 코너',
      destination: { x: 0.82, y: 0.24 },
      start: { x: 0.45, y: 0.05 },
      waypoints: [
        { x: 0.45, y: 0.05 },
        { x: 0.82, y: 0.05 },
        { x: 0.82, y: 0.24 },
      ],
    },
    selectedProduct: {
      id: 1, rank: 1, name: '대용량 물티슈', price: 1000,
      image_url: '/img.jpg', category_major: '뷰티/위생',
      category_middle: '화장지/물티슈', score: 0.95,
      counter_number: 7, destination_x: 0.82, destination_y: 0.24,
      location_floor: 'B1', location_description: '화장품 코너',
    },
  });
});

describe('MapScreen', () => {
  it('should render map title', () => {
    render(<MapScreen />);
    expect(screen.getByText('매장 지도')).toBeInTheDocument();
  });

  it('should show counter number in location text', () => {
    render(<MapScreen />);
    expect(screen.getByText(/7번 매대/)).toBeInTheDocument();
  });

  it('should show floor label', () => {
    render(<MapScreen />);
    expect(screen.getByText(/지하1층/)).toBeInTheDocument();
  });

  it('should render reset button', () => {
    render(<MapScreen />);
    expect(screen.getByText('다시 검색하기')).toBeInTheDocument();
  });

  it('should reset on button click', () => {
    render(<MapScreen />);
    fireEvent.click(screen.getByText('다시 검색하기'));
    expect(useAppStore.getState().screen).toBe('home');
  });

  it('should show QR scan description', () => {
    render(<MapScreen />);
    expect(screen.getByText(/QR코드를 스캔하면/)).toBeInTheDocument();
  });

  it('should render logo', () => {
    render(<MapScreen />);
    expect(screen.getByAltText('어디다이소')).toBeInTheDocument();
  });
});
