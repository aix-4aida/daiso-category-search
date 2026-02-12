type SpeechCallback = (transcript: string) => void;

const SpeechRecognition =
  typeof window !== 'undefined'
    ? (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition
    : null;

export function isSpeechSupported(): boolean {
  return SpeechRecognition != null;
}

interface SpeechRecognitionEvent {
  results: { [key: number]: { [key: number]: { transcript: string } } };
}

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start(): void;
  stop(): void;
}

let recognition: SpeechRecognitionInstance | null = null;

export function startListening(onResult: SpeechCallback, onEnd?: () => void): void {
  if (!SpeechRecognition) return;

  recognition = new (SpeechRecognition as unknown as new () => SpeechRecognitionInstance)();
  recognition.lang = 'ko-KR';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    const transcript = event.results[0][0].transcript;
    onResult(transcript);
  };

  recognition.onend = () => {
    onEnd?.();
  };

  recognition.onerror = () => {
    onEnd?.();
  };

  recognition.start();
}

export function stopListening(): void {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
}
