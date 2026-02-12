import type { Product } from '../types';

interface ProductCardProps {
  product: Product;
  isTop?: boolean;
  onSelect: (product: Product) => void;
}

export default function ProductCard({ product, isTop = false, onSelect }: ProductCardProps) {
  return (
    <button
      onClick={() => onSelect(product)}
      className={`flex flex-col items-center p-4 rounded-2xl transition-all
                  hover:shadow-lg active:scale-[0.98] cursor-pointer
                  ${isTop
                    ? 'bg-white ring-2 ring-daiso-red shadow-md scale-105'
                    : 'bg-white shadow'
                  }`}
      aria-label={`${product.name} 위치 보기`}
    >
      {isTop && (
        <span className="self-start bg-daiso-red text-white text-xs font-bold px-2 py-1 rounded-full mb-2">
          BEST
        </span>
      )}
      <div className="w-32 h-32 mb-3 overflow-hidden rounded-xl bg-daiso-gray-50">
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-full object-contain"
          loading="lazy"
        />
      </div>
      <h3 className="text-base font-bold text-daiso-gray-900 text-center leading-tight mb-1">
        {product.name}
      </h3>
      <p className="text-xs text-daiso-gray-500 mb-2">
        {product.category_major} &gt; {product.category_middle}
      </p>
      <p className="text-lg font-extrabold text-daiso-red">
        {product.price.toLocaleString()}원
      </p>
    </button>
  );
}
