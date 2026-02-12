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
    <form onSubmit={handleSubmit} className="w-full max-w-xl">
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="상품 이름을 말해주세요"
          className="flex-1 h-14 px-6 text-lg rounded-full border-2 border-daiso-gray-200
                     focus:border-daiso-red focus:outline-none
                     font-suite placeholder:text-daiso-gray-500"
          aria-label="상품 검색"
        />
        <button
          type="submit"
          className="h-14 px-8 bg-daiso-red text-white text-lg font-bold
                     rounded-full hover:bg-daiso-red-dark active:scale-95
                     transition-all"
        >
          검색
        </button>
      </div>
    </form>
  );
}
