import { useEffect, useRef } from 'react';
import { useAppStore } from '../stores/useAppStore';

const IDLE_TIMEOUT = 60_000; // 60 seconds

export default function IdleTimer() {
  const screen = useAppStore((s) => s.screen);
  const reset = useAppStore((s) => s.reset);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (screen === 'home') return;

    const resetTimer = () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(reset, IDLE_TIMEOUT);
    };

    const events = ['touchstart', 'mousedown', 'keydown'] as const;
    events.forEach((e) => window.addEventListener(e, resetTimer));
    resetTimer();

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      events.forEach((e) => window.removeEventListener(e, resetTimer));
    };
  }, [screen, reset]);

  return null;
}
