import React, { useState, useEffect } from 'react';
import { ScriptData, VideoState, ScriptBlock } from '../types/script';
import { Play, Pause, SkipBack, SkipForward, Square, X } from 'lucide-react';
import { AudioService } from '../services/audioService';
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

interface VideoPlayerProps {
  scriptData: ScriptData;
  sessionFolder?: string;
  onExit?: () => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ scriptData, sessionFolder, onExit }) => {
  const [videoState, setVideoState] = useState<VideoState>({
    currentBlock: 0,
    isPlaying: false,
    isPaused: false,
    playbackSpeed: 1.0
  });
  const [autoPlay, setAutoPlay] = useState(true);
  const [autoPlayDelay, setAutoPlayDelay] = useState('1000'); // 1 second delay between blocks

  const [audioService] = useState(() => new AudioService());
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Set session folder on audio service if available
    if (sessionFolder) {
      audioService.setSessionFolder(sessionFolder);
    }

    // Stop audio when component unmounts
    return () => {
      audioService.stopCurrentAudio();
    };
  }, [audioService, sessionFolder]);

  useEffect(() => {
    // Update playback speed when it changes
    audioService.setPlaybackSpeed(videoState.playbackSpeed);
  }, [videoState.playbackSpeed, audioService]);

  useEffect(() => {
    // Handle autoplay when flag is set
    if (videoState.shouldAutoPlay && !videoState.isPlaying) {
      setVideoState(prev => ({ ...prev, shouldAutoPlay: false }));
      handlePlay();
    }
  }, [videoState.shouldAutoPlay, videoState.currentBlock]);

  const getCurrentBlockText = (): string => {
    const currentBlock = getCurrentBlock();
    if (!currentBlock) return '';

    return currentBlock.markdown;
  };

  const handlePlay = async () => {
    const currentBlock = getCurrentBlock();
    if (!currentBlock || videoState.isPlaying) return;

    setIsAudioLoading(true);
    setError(null);

    try {
      setVideoState(prev => ({ ...prev, isPlaying: true, isPaused: false }));

      // Check if we have pre-generated audio URLs from the response
      if (scriptData.audio_files && scriptData.audio_files[videoState.currentBlock]) {
        const audioUrl = scriptData.audio_files[videoState.currentBlock];
        await audioService.playAudioFromUrl(audioUrl, videoState.playbackSpeed);
      } else {
        // Check if we have a pre-generated audio file from session
        const audioFile = (currentBlock as any).audio_file;
        if (sessionFolder && audioFile) {
          await audioService.playAudioFromSession(audioFile, videoState.playbackSpeed);
        } else {
          // Fallback to generating audio from text
          const blockText = getCurrentBlockText();
          await audioService.playAudio(blockText, videoState.playbackSpeed);
        }
      }

      // Audio finished playing
      setVideoState(prev => ({ ...prev, isPlaying: false, isPaused: false }));

      // Auto-advance to next block if autoPlay is enabled
      if (autoPlay && videoState.currentBlock < scriptData.script.length - 1) {
        setTimeout(() => {
          setVideoState(prev => ({
            ...prev,
            currentBlock: prev.currentBlock + 1,
            shouldAutoPlay: true  // Flag to trigger autoplay in useEffect
          }));
        }, parseInt(autoPlayDelay));
      }
    } catch (err) {
      setError(`Audio playback failed: ${err}`);
      setVideoState(prev => ({ ...prev, isPlaying: false, isPaused: false }));
    } finally {
      setIsAudioLoading(false);
    }
  };

  const handlePause = () => {
    audioService.pauseCurrentAudio();
    setVideoState(prev => ({ ...prev, isPlaying: false, isPaused: true }));
  };

  const handleStop = () => {
    audioService.stopCurrentAudio();
    setVideoState(prev => ({
      ...prev,
      isPlaying: false,
      isPaused: false,
      currentBlock: 0,
      shouldAutoPlay: false
    }));
    setIsAudioLoading(false);
    setError(null);
  };

  const handlePrevious = () => {
    audioService.stopCurrentAudio();
    setVideoState(prev => ({
      ...prev,
      currentBlock: Math.max(0, prev.currentBlock - 1),
      isPlaying: false,
      isPaused: false
    }));
    setIsAudioLoading(false);
  };

  const handleNext = () => {
    audioService.stopCurrentAudio();
    setVideoState(prev => ({
      ...prev,
      currentBlock: Math.min(scriptData.script.length - 1, prev.currentBlock + 1),
      isPlaying: false,
      isPaused: false
    }));
    setIsAudioLoading(false);
  };

  const getCurrentBlock = (): ScriptBlock | null => {
    return scriptData.script[videoState.currentBlock] || null;
  };

  const currentBlock = getCurrentBlock();

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
            <Button variant="outline" onClick={handlePrevious} disabled={videoState.currentBlock === 0}>
              <SkipBack size={20} />
            </Button>

            {videoState.isPlaying ? (
              <Button onClick={handlePause} className="play-pause-btn" disabled={isAudioLoading}>
                <Pause size={24} />
              </Button>
            ) : (
              <Button onClick={handlePlay} className="play-pause-btn" disabled={isAudioLoading}>
                {isAudioLoading ? '...' : <Play size={24} />}
              </Button>
            )}

            <Button variant="destructive" onClick={handleStop}>
              <Square size={20} />
            </Button>

            <Button variant="outline" onClick={handleNext} disabled={videoState.currentBlock === scriptData.script.length - 1}>
              <SkipForward size={20} />
            </Button>
          </div>

          <div className="flex items-center gap-2 flex-1">
            <Label className="flex-shrink-0">
              {videoState.currentBlock + 1} / {scriptData.script.length}
            </Label>
            <Progress value={((videoState.currentBlock + 1) / scriptData.script.length) * 100} />
          </div>

          <div className="flex items-center gap-2">
            <Select value={videoState.playbackSpeed.toString()} onValueChange={(value) => setVideoState(prev => ({
              ...prev,
              playbackSpeed: parseFloat(value)
            }))}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Speed" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.5">0.5x</SelectItem>
                <SelectItem value="1.0">1.0x</SelectItem>
                <SelectItem value="1.25">1.25x</SelectItem>
                <SelectItem value="1.5">1.5x</SelectItem>
                <SelectItem value="2.0">2.0x</SelectItem>
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
                  onValueChange={(value) => setAutoPlayDelay(value)}
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
