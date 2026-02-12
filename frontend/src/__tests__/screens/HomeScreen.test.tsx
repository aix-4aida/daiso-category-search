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
  it('should render title', () => {
    render(<HomeScreen />);
    expect(screen.getByText('어디다있소')).toBeInTheDocument();
  });

  it('should render search bar', () => {
    render(<HomeScreen />);
    expect(screen.getByLabelText('상품 검색')).toBeInTheDocument();
  });

  it('should render mic button', () => {
    render(<HomeScreen />);
    expect(screen.getByLabelText('음성으로 검색')).toBeInTheDocument();
  });

  it('should render category chips', () => {
    render(<HomeScreen />);
    expect(screen.getByText('물티슈')).toBeInTheDocument();
    expect(screen.getByText('수납함')).toBeInTheDocument();
  });

  it('should show error message when error exists', () => {
    useAppStore.setState({ error: '검색 결과가 없습니다.' });
    render(<HomeScreen />);
    expect(screen.getByRole('alert')).toHaveTextContent('검색 결과가 없습니다.');
  });
});
