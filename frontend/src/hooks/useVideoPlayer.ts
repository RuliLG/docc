import { useState, useCallback, useMemo } from 'react';
import { VideoState, ScriptData } from '../types/script';

interface UseVideoPlayerProps {
  scriptData: ScriptData;
}

export const useVideoPlayer = ({ scriptData }: UseVideoPlayerProps) => {
  const [currentBlockIndex, setCurrentBlockIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [shouldAutoPlay, setShouldAutoPlay] = useState(false);

  const currentBlock = useMemo(
    () => scriptData.script[currentBlockIndex] || null,
    [scriptData.script, currentBlockIndex]
  );

  const goToPrevious = useCallback(() => {
    setCurrentBlockIndex(prev => Math.max(0, prev - 1));
    setShouldAutoPlay(false);
  }, []);

  const goToNext = useCallback(() => {
    setCurrentBlockIndex(prev => Math.min(scriptData.script.length - 1, prev + 1));
    setShouldAutoPlay(false);
  }, [scriptData.script.length]);

  const goToStart = useCallback(() => {
    setCurrentBlockIndex(0);
    setShouldAutoPlay(false);
  }, []);

  const triggerAutoPlay = useCallback(() => {
    setShouldAutoPlay(true);
  }, []);

  const clearAutoPlay = useCallback(() => {
    setShouldAutoPlay(false);
  }, []);

  return {
    currentBlockIndex,
    currentBlock,
    playbackSpeed,
    shouldAutoPlay,
    setPlaybackSpeed,
    goToPrevious,
    goToNext,
    goToStart,
    triggerAutoPlay,
    clearAutoPlay,
  };
};