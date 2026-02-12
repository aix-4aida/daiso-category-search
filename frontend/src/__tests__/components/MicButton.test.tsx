import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MicButton from '../../components/MicButton';

vi.mock('../../services/speech', () => ({
  isSpeechSupported: vi.fn(() => true),
  startListening: vi.fn(),
  stopListening: vi.fn(),
}));

import { isSpeechSupported } from '../../services/speech';

describe('MicButton', () => {
  beforeEach(() => {
    vi.mocked(isSpeechSupported).mockReturnValue(true);
  });

  it('should render mic button when speech is supported', () => {
    render(<MicButton />);
    expect(screen.getByLabelText('음성으로 검색')).toBeInTheDocument();
  });

  it('should not render when speech is not supported', () => {
    vi.mocked(isSpeechSupported).mockReturnValue(false);
    const { container } = render(<MicButton />);
    expect(container.firstChild).toBeNull();
  });

  it('should be clickable', () => {
    render(<MicButton />);
    const button = screen.getByLabelText('음성으로 검색');
    expect(button).toBeEnabled();
    fireEvent.click(button);
  });
});
