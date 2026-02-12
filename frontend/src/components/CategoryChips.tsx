const POPULAR_CATEGORIES = [
  '물티슈', '수납함', '주방용품', '문구', '청소', '건전지', '양말', '과자',
];

interface CategoryChipsProps {
  onSelect: (query: string) => void;
}

export default function CategoryChips({ onSelect }: CategoryChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2 max-w-lg">
      {POPULAR_CATEGORIES.map((cat) => (
        <button
          key={cat}
          onClick={() => onSelect(cat)}
          className="px-4 py-2 rounded-full bg-daiso-gray-100 text-sm font-medium
                     text-daiso-gray-700 hover:bg-daiso-red hover:text-white
                     active:scale-95 transition-all"
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
