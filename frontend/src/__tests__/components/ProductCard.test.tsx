import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ProductCard from '../../components/ProductCard';
import type { Product } from '../../types';

const mockProduct: Product = {
  id: 1,
  rank: 1,
  name: '대용량 물티슈',
  price: 1000,
  image_url: '/static/images/001.jpg',
  category_major: '뷰티/위생',
  category_middle: '화장지/물티슈',
  score: 0.95,
};

describe('ProductCard', () => {
  it('should render product info', () => {
    render(<ProductCard product={mockProduct} onSelect={() => {}} />);
    expect(screen.getByText('대용량 물티슈')).toBeInTheDocument();
    expect(screen.getByText(/뷰티\/위생/)).toBeInTheDocument();
  });

  it('should show BEST! badge when isTop', () => {
    render(<ProductCard product={mockProduct} isTop onSelect={() => {}} />);
    expect(screen.getByText('BEST!')).toBeInTheDocument();
  });

  it('should not show BEST! badge by default', () => {
    render(<ProductCard product={mockProduct} onSelect={() => {}} />);
    expect(screen.queryByText('BEST!')).not.toBeInTheDocument();
  });

  it('should call onSelect when clicked', () => {
    const onSelect = vi.fn();
    render(<ProductCard product={mockProduct} onSelect={onSelect} />);
    fireEvent.click(screen.getByLabelText('대용량 물티슈 위치 보기'));
    expect(onSelect).toHaveBeenCalledWith(mockProduct);
  });

  it('should render product image', () => {
    render(<ProductCard product={mockProduct} onSelect={() => {}} />);
    const img = screen.getByAltText('대용량 물티슈');
    expect(img).toHaveAttribute('src', '/static/images/001.jpg');
  });
});
