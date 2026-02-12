import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MapScreen from '../../screens/MapScreen';
import { useAppStore } from '../../stores/useAppStore';

beforeEach(() => {
  useAppStore.setState({
    screen: 'map',
    mapInfo: { floor: '1F', section: '뷰티/위생', map_image: '/static/maps/store.png' },
    selectedProduct: {
      id: 1, rank: 1, name: '대용량 물티슈', price: 1000,
      image_url: '/img.jpg', category_major: '뷰티/위생',
      category_middle: '화장지/물티슈', score: 0.95,
    },
  });
});

describe('MapScreen', () => {
  it('should render map title', () => {
    render(<MapScreen />);
    expect(screen.getByText('매장 위치 안내')).toBeInTheDocument();
  });

  it('should show product info on map', () => {
    render(<MapScreen />);
    expect(screen.getByText('대용량 물티슈')).toBeInTheDocument();
    expect(screen.getByText(/뷰티\/위생/)).toBeInTheDocument();
  });

  it('should render back and reset buttons', () => {
    render(<MapScreen />);
    expect(screen.getByText('결과로 돌아가기')).toBeInTheDocument();
    expect(screen.getByText('다시 검색하기')).toBeInTheDocument();
  });

  it('should go back to results on button click', () => {
    render(<MapScreen />);
    fireEvent.click(screen.getByText('결과로 돌아가기'));
    expect(useAppStore.getState().screen).toBe('results');
  });

  it('should reset on button click', () => {
    render(<MapScreen />);
    fireEvent.click(screen.getByText('다시 검색하기'));
    expect(useAppStore.getState().screen).toBe('home');
  });
});
