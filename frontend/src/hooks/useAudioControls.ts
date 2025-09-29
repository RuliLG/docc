import { useState, useCallback, useEffect } from 'react';
import { AudioService } from '../services/audioService';
import { ScriptData, ScriptBlock } from '../types/script';

interface UseAudioControlsProps {
  scriptData: ScriptData;
  currentBlock: ScriptBlock | null;
  currentBlockIndex: number;
  sessionFolder?: string;
  playbackSpeed: number;
  onBlockComplete?: () => void;
}

export const useAudioControls = ({
  scriptData,
  currentBlock,
  currentBlockIndex,
  sessionFolder,
  playbackSpeed,
  onBlockComplete,
}: UseAudioControlsProps) => {
  const [audioService] = useState(() => new AudioService());
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionFolder) {
      audioService.setSessionFolder(sessionFolder);
    }

    return () => {
      audioService.stopCurrentAudio();
    };
  }, [audioService, sessionFolder]);

  useEffect(() => {
    audioService.setPlaybackSpeed(playbackSpeed);
  }, [playbackSpeed, audioService]);

  const play = useCallback(async () => {
    if (!currentBlock || isPlaying) return;

    setIsLoading(true);
    setError(null);

    try {
      setIsPlaying(true);
      setIsPaused(false);

      if (scriptData.audio_files && scriptData.audio_files[currentBlockIndex]) {
        const audioUrl = scriptData.audio_files[currentBlockIndex];
        await audioService.playAudioFromUrl(audioUrl, playbackSpeed);
      } else {
        const audioFile = (currentBlock as any).audio_file;
        if (sessionFolder && audioFile) {
          await audioService.playAudioFromSession(audioFile, playbackSpeed);
        } else {
          await audioService.playAudio(currentBlock.markdown, playbackSpeed);
        }
      }

      setIsPlaying(false);
      setIsPaused(false);
      onBlockComplete?.();
    } catch (err) {
      setError(`Audio playback failed: ${err}`);
      setIsPlaying(false);
      setIsPaused(false);
    } finally {
      setIsLoading(false);
    }
  }, [currentBlock, isPlaying, currentBlockIndex, playbackSpeed, scriptData.audio_files, audioService, sessionFolder, onBlockComplete]);

  const pause = useCallback(() => {
    audioService.pauseCurrentAudio();
    setIsPlaying(false);
    setIsPaused(true);
  }, [audioService]);

  const stop = useCallback(() => {
    audioService.stopCurrentAudio();
    setIsPlaying(false);
    setIsPaused(false);
    setIsLoading(false);
    setError(null);
  }, [audioService]);

  return {
    play,
    pause,
    stop,
    isPlaying,
    isPaused,
    isLoading,
    error,
    setError,
  };
};
