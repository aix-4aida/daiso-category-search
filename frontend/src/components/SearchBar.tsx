import { useState, type FormEvent } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  initialValue?: string;
}

export default function SearchBar({ onSearch, initialValue = '' }: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed) {
      onSearch(trimmed);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex-1">
      <div className="flex items-center h-12 rounded-full border border-gray-300 bg-white px-5 gap-3
                      focus-within:border-daiso-red transition-colors">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="찾으시는 상품을 말씀해주세요 (예. 욕실 슬리퍼, 요가 매트)"
          className="flex-1 text-sm bg-transparent outline-none placeholder:text-gray-400
                     font-suite"
          aria-label="상품 검색"
        />
        <button type="submit" className="text-gray-400 hover:text-daiso-red transition-colors" aria-label="검색">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
