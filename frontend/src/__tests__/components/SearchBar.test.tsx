import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchBar from '../../components/SearchBar';

describe('SearchBar', () => {
  it('should render input and button', () => {
    render(<SearchBar onSearch={() => {}} />);
    expect(screen.getByLabelText('상품 검색')).toBeInTheDocument();
    expect(screen.getByLabelText('검색')).toBeInTheDocument();
  });

  it('should call onSearch with trimmed value on submit', () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByLabelText('상품 검색');
    fireEvent.change(input, { target: { value: '  물티슈  ' } });
    fireEvent.submit(input.closest('form')!);

    expect(onSearch).toHaveBeenCalledWith('물티슈');
  });

  it('should not call onSearch with empty value', () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);

    fireEvent.submit(screen.getByLabelText('검색').closest('form')!);
    expect(onSearch).not.toHaveBeenCalled();
  });

  it('should display placeholder text', () => {
    render(<SearchBar onSearch={() => {}} />);
    expect(screen.getByPlaceholderText(/찾으시는 상품을 말씀해주세요/)).toBeInTheDocument();
  });

  it('should accept initial value', () => {
    render(<SearchBar onSearch={() => {}} initialValue="볼펜" />);
    expect(screen.getByLabelText('상품 검색')).toHaveValue('볼펜');
  });
});
