import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResultsScreen from '../../screens/ResultsScreen';
import { useAppStore } from '../../stores/useAppStore';

beforeEach(() => {
  useAppStore.setState({
    results: [
      {
        id: 1, rank: 1, name: '대용량 물티슈', price: 1000,
        image_url: '/img.jpg', category_major: '뷰티/위생',
        category_middle: '화장지/물티슈', score: 0.95,
      },
      {
        id: 2, rank: 2, name: '아기 물티슈', price: 1500,
        image_url: '/img2.jpg', category_major: '뷰티/위생',
        category_middle: '화장지/물티슈', score: 0.88,
      },
    ],
    queryInfo: { original: '물티슈', intent: 'search', keywords: ['물티슈'] },
  });
});

describe('ResultsScreen', () => {
  it('should render product cards', () => {
    render(<ResultsScreen />);
    expect(screen.getByText('대용량 물티슈')).toBeInTheDocument();
    expect(screen.getByText('아기 물티슈')).toBeInTheDocument();
  });

  it('should show query info', () => {
    render(<ResultsScreen />);
    expect(screen.getByText(/물티슈.*검색 결과/)).toBeInTheDocument();
  });

  it('should render reset button', () => {
    render(<ResultsScreen />);
    expect(screen.getByText('다시 검색하기')).toBeInTheDocument();
  });

  it('should reset on button click', () => {
    render(<ResultsScreen />);
    fireEvent.click(screen.getByText('다시 검색하기'));
    expect(useAppStore.getState().screen).toBe('home');
  });

  it('should mark first card as top', () => {
    render(<ResultsScreen />);
    expect(screen.getByText('BEST')).toBeInTheDocument();
  });
});
