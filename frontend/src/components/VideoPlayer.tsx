import React, { useState, useEffect, useCallback } from 'react';
import { ScriptData } from '../types/script';
import { Play, Pause, SkipBack, SkipForward, Square, X } from 'lucide-react';
import TextRenderer from './TextRenderer';
import CodeRenderer from './CodeRenderer';
import { Card, CardContent, CardDescription } from './ui/card';
import TitleH1 from './ui/TitleH1';
import { Button } from './ui/button';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Progress } from './ui/progress';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { useVideoPlayer } from '../hooks/useVideoPlayer';
import { useAudioControls } from '../hooks/useAudioControls';

interface VideoPlayerProps {
  scriptData: ScriptData;
  sessionFolder?: string;
  onExit?: () => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ scriptData, sessionFolder, onExit }) => {
  const [autoPlay, setAutoPlay] = useState(true);
  const [autoPlayDelay, setAutoPlayDelay] = useState(1000);

  const {
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
  } = useVideoPlayer({ scriptData });

  const handleBlockComplete = useCallback(() => {
    if (autoPlay && currentBlockIndex < scriptData.script.length - 1) {
      setTimeout(() => {
        goToNext();
        triggerAutoPlay();
      }, autoPlayDelay);
    }
  }, [autoPlay, currentBlockIndex, scriptData.script.length, autoPlayDelay, goToNext, triggerAutoPlay]);

  const {
    play,
    pause,
    stop,
    isPlaying,
    isPaused,
    isLoading,
    error,
    setError,
  } = useAudioControls({
    scriptData,
    currentBlock,
    currentBlockIndex,
    sessionFolder,
    playbackSpeed,
    onBlockComplete: handleBlockComplete,
  });

  useEffect(() => {
    if (shouldAutoPlay && !isPlaying) {
      clearAutoPlay();
      play();
    }
  }, [shouldAutoPlay, isPlaying, clearAutoPlay, play]);

  const handleStop = useCallback(() => {
    stop();
    goToStart();
  }, [stop, goToStart]);

  const handlePrevious = useCallback(() => {
    stop();
    goToPrevious();
  }, [stop, goToPrevious]);

  const handleNext = useCallback(() => {
    stop();
    goToNext();
  }, [stop, goToNext]);

  return (
    <div className="h-screen w-screen p-2 space-y-2 grid grid-rows-[auto_1fr_auto]">
      <Card>
        <CardContent className="flex justify-between items-center">
          <div className="flex flex-col gap-2">
            <TitleH1>{scriptData.question}</TitleH1>
            <CardDescription className="repository-path">Repository: {scriptData.repository_path}</CardDescription>
          </div>
          {onExit && (
            <Button variant="outline" onClick={onExit} title="Exit and return to form">
              <X size={24} />
            </Button>
          )}
        </CardContent>
      </Card>

      <Card className="overflow-y-auto">
        <CardContent>
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
              <Button className="absolute top-2 right-2" variant="outline" onClick={() => setError(null)}><X size={20} /></Button>
            </Alert>
          )}

          {currentBlock && (
            <div className="block-container">
              {currentBlock.type === 'text' ? (
                <TextRenderer block={currentBlock} />
              ) : (
                <CodeRenderer block={currentBlock} />
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center gap-8">
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrevious} disabled={currentBlockIndex === 0}>
              <SkipBack size={20} />
            </Button>

            {isPlaying ? (
              <Button onClick={pause} className="play-pause-btn">
                <Pause size={24} />
              </Button>
            ) : (
              <Button onClick={play} className="play-pause-btn">
                <Play size={24} />
              </Button>
            )}

            <Button variant="destructive" onClick={handleStop}>
              <Square size={20} />
            </Button>

            <Button variant="outline" onClick={handleNext} disabled={currentBlockIndex === scriptData.script.length - 1}>
              <SkipForward size={20} />
            </Button>
          </div>

          <div className="flex items-center gap-2 flex-1">
            <Label className="flex-shrink-0">
              {currentBlockIndex + 1} / {scriptData.script.length}
            </Label>
            <Progress value={((currentBlockIndex + 1) / scriptData.script.length) * 100} />
          </div>

          <div className="flex items-center gap-2">
            <Select
              value={playbackSpeed.toString()}
              onValueChange={(value) => setPlaybackSpeed(parseFloat(value))}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Speed" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.5">0.5x</SelectItem>
                <SelectItem value="1">1.0x</SelectItem>
                <SelectItem value="1.25">1.25x</SelectItem>
                <SelectItem value="1.5">1.5x</SelectItem>
                <SelectItem value="2">2.0x</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Label>
              <Input
                type="checkbox"
                id="auto-play-control"
                className="h-4 w-4"
                checked={autoPlay}
                onChange={(e) => setAutoPlay(e.target.checked)}
              />
              Auto-play
            </Label>
            {autoPlay && (
              <Label>
                Delay:
                <Select
                  value={autoPlayDelay.toString()}
                  onValueChange={(value) => setAutoPlayDelay(parseInt(value, 10))}
                >
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Delay" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">No delay</SelectItem>
                    <SelectItem value="500">0.5s</SelectItem>
                    <SelectItem value="1000">1s</SelectItem>
                    <SelectItem value="2000">2s</SelectItem>
                    <SelectItem value="3000">3s</SelectItem>
                  </SelectContent>
                </Select>
              </Label>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VideoPlayer;