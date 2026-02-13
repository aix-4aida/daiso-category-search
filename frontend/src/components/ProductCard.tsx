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
      className={`flex flex-col items-center p-6 rounded-3xl transition-all
                  hover:shadow-lg active:scale-[0.98] cursor-pointer bg-white
                  ${isTop
                    ? 'border-3 border-dashed border-daiso-red w-80'
                    : 'border border-gray-200 w-64'
                  }`}
      aria-label={`${product.name} 위치 보기`}
    >
      {isTop && (
        <span className="text-daiso-red text-sm font-extrabold tracking-wider mb-3">
          BEST!
        </span>
      )}
      <div className={`mb-4 overflow-hidden rounded-xl bg-gray-50
                       ${isTop ? 'w-48 h-48' : 'w-36 h-36'}`}>
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-full object-contain"
          loading="lazy"
        />
      </div>
      <h3 className={`font-bold text-daiso-gray-900 text-center leading-tight mb-2
                       ${isTop ? 'text-lg' : 'text-base'}`}>
        {product.name}
      </h3>
      <p className="text-xs text-gray-400">
        {product.category_major} &gt; {product.category_middle}
      </p>
    </button>
  );
}
