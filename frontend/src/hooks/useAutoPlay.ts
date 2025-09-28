import { useEffect, useCallback } from 'react';

interface UseAutoPlayProps {
  enabled: boolean;
  delay: number;
  currentBlock: number;
  totalBlocks: number;
  isPlaying: boolean;
  onNext: () => void;
  onAutoPlayNext: () => void;
}

export const useAutoPlay = ({
  enabled,
  delay,
  currentBlock,
  totalBlocks,
  isPlaying,
  onNext,
  onAutoPlayNext,
}: UseAutoPlayProps) => {
  const shouldAutoAdvance = useCallback(() => {
    return enabled && currentBlock < totalBlocks - 1;
  }, [enabled, currentBlock, totalBlocks]);

  useEffect(() => {
    if (!isPlaying && shouldAutoAdvance()) {
      const timer = setTimeout(() => {
        onNext();
        onAutoPlayNext();
      }, delay);

      return () => clearTimeout(timer);
    }
  }, [isPlaying, shouldAutoAdvance, onNext, onAutoPlayNext, delay]);
};