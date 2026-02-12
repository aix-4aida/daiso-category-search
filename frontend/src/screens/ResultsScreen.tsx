import { useAppStore } from '../stores/useAppStore';
import ProductCard from '../components/ProductCard';

export default function ResultsScreen() {
  const results = useAppStore((s) => s.results);
  const queryInfo = useAppStore((s) => s.queryInfo);
  const selectProduct = useAppStore((s) => s.selectProduct);
  const reset = useAppStore((s) => s.reset);

  return (
    <div className="flex flex-col items-center min-h-screen bg-daiso-gray-50 px-6 py-10">
      {/* Query info */}
      {queryInfo && (
        <p className="text-daiso-gray-500 mb-6 text-center">
          &ldquo;{queryInfo.original}&rdquo; 검색 결과
        </p>
      )}

      {/* Product cards */}
      <div className="flex items-start justify-center gap-6 mb-10 flex-wrap">
        {results.map((product, index) => (
          <ProductCard
            key={product.id}
            product={product}
            isTop={index === 0}
            onSelect={selectProduct}
          />
        ))}
      </div>

      {/* Actions */}
      <button
        onClick={reset}
        className="px-8 py-3 rounded-full bg-daiso-gray-200 text-daiso-gray-700
                   font-bold hover:bg-daiso-gray-500 hover:text-white
                   active:scale-95 transition-all"
      >
        다시 검색하기
      </button>
    </div>
  );
}
