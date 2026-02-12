import { useAppStore } from '../stores/useAppStore';
import { isSpeechSupported, startListening, stopListening } from '../services/speech';

export default function MicButton() {
  const isListening = useAppStore((s) => s.isListening);
  const setListening = useAppStore((s) => s.setListening);
  const search = useAppStore((s) => s.search);

  if (!isSpeechSupported()) return null;

  const handleClick = () => {
    if (isListening) {
      stopListening();
      setListening(false);
    } else {
      setListening(true);
      startListening(
        (transcript) => {
          setListening(false);
          search(transcript);
        },
        () => setListening(false),
      );
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`relative w-20 h-20 rounded-full flex items-center justify-center
                  transition-all ${
                    isListening
                      ? 'bg-daiso-red scale-110'
                      : 'bg-daiso-red hover:bg-daiso-red-dark'
                  }`}
      aria-label={isListening ? '음성 인식 중지' : '음성으로 검색'}
    >
      {isListening && (
        <span
          className="absolute inset-0 rounded-full bg-daiso-red opacity-50"
          style={{ animation: 'pulse-ring 1.5s ease-out infinite' }}
        />
      )}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="white"
        className="w-10 h-10 relative z-10"
      >
        <path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3z" />
        <path d="M17 11a1 1 0 10-2 0 3 3 0 11-6 0 1 1 0 10-2 0 5 5 0 004 4.9V18H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.1A5 5 0 0017 11z" />
      </svg>
    </button>
  );
}
