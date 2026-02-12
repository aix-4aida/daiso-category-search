import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingScreen from '../../screens/LoadingScreen';
import { useAppStore } from '../../stores/useAppStore';

beforeEach(() => {
  useAppStore.getState().reset();
});

describe('LoadingScreen', () => {
  it('should render loading message', () => {
    render(<LoadingScreen />);
    expect(screen.getByText('매장 내 상품 위치를 찾고 있습니다...')).toBeInTheDocument();
  });

  it('should show query text', () => {
    useAppStore.setState({ query: '물티슈' });
    render(<LoadingScreen />);
    expect(screen.getByText(/물티슈/)).toBeInTheDocument();
  });

  it('should show patience message', () => {
    render(<LoadingScreen />);
    expect(screen.getByText('잠시만 기다려주세요')).toBeInTheDocument();
  });
});
