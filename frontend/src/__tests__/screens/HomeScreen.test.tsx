import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import HomeScreen from '../../screens/HomeScreen';
import { useAppStore } from '../../stores/useAppStore';

vi.mock('../../services/speech', () => ({
  isSpeechSupported: vi.fn(() => true),
  startListening: vi.fn(),
  stopListening: vi.fn(),
}));

beforeEach(() => {
  useAppStore.getState().reset();
});

describe('HomeScreen', () => {
  it('should render logo', () => {
    render(<HomeScreen />);
    expect(screen.getByAltText('어디다이소')).toBeInTheDocument();
  });

  it('should render search bar', () => {
    render(<HomeScreen />);
    expect(screen.getByLabelText('상품 검색')).toBeInTheDocument();
  });

  it('should render mic button', () => {
    render(<HomeScreen />);
    expect(screen.getByLabelText('음성으로 검색')).toBeInTheDocument();
  });

  it('should render banner image', () => {
    render(<HomeScreen />);
    const banner = screen.getByAltText('설연휴 쇼핑도 다이소에서');
    expect(banner).toHaveAttribute('src', '/banner01.png');
  });

  it('should show error view when error exists', () => {
    useAppStore.setState({ error: '검색 결과가 없습니다.' });
    render(<HomeScreen />);
    expect(screen.getByText('죄송합니다')).toBeInTheDocument();
    expect(screen.getByText('다시 검색하기')).toBeInTheDocument();
  });

  it('should show suggestion examples on error', () => {
    useAppStore.setState({ error: '검색 결과가 없습니다.' });
    render(<HomeScreen />);
    expect(screen.getByText(/이렇게 검색해 보세요/)).toBeInTheDocument();
  });
});
