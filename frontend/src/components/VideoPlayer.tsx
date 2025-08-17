import React, { useState, useEffect } from 'react';
import { ScriptData, VideoState, ScriptBlock } from '../types/script';
import { Play, Pause, SkipBack, SkipForward, Square } from 'lucide-react';
import { AudioService } from '../services/audioService';
import TextRenderer from './TextRenderer';
import CodeRenderer from './CodeRenderer';
import './VideoPlayer.css';

interface VideoPlayerProps {
  scriptData: ScriptData;
  sessionFolder?: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ scriptData, sessionFolder }) => {
  const [videoState, setVideoState] = useState<VideoState>({
    currentBlock: 0,
    isPlaying: false,
    isPaused: false,
    playbackSpeed: 1.0
  });
  const [autoPlay, setAutoPlay] = useState(true);
  const [autoPlayDelay, setAutoPlayDelay] = useState(1000); // 1 second delay between blocks

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
        }, autoPlayDelay);
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
    <div className="video-player">
      <div className="video-header">
        <h2>{scriptData.question}</h2>
        <p className="repository-path">Repository: {scriptData.repository_path}</p>
      </div>

      <div className="video-content">
        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={() => setError(null)}>×</button>
          </div>
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
      </div>

      <div className="video-controls">
        <div className="control-buttons">
          <button onClick={handlePrevious} disabled={videoState.currentBlock === 0}>
            <SkipBack size={20} />
          </button>

          {videoState.isPlaying ? (
            <button onClick={handlePause} className="play-pause-btn" disabled={isAudioLoading}>
              <Pause size={24} />
            </button>
          ) : (
            <button onClick={handlePlay} className="play-pause-btn" disabled={isAudioLoading}>
              {isAudioLoading ? '...' : <Play size={24} />}
            </button>
          )}

          <button onClick={handleStop}>
            <Square size={20} />
          </button>

          <button
            onClick={handleNext}
            disabled={videoState.currentBlock === scriptData.script.length - 1}
          >
            <SkipForward size={20} />
          </button>
        </div>

        <div className="progress-info">
          <span className="block-counter">
            {videoState.currentBlock + 1} / {scriptData.script.length}
          </span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${((videoState.currentBlock + 1) / scriptData.script.length) * 100}%`
              }}
            />
          </div>
        </div>

        <div className="speed-control">
          <label>Speed: </label>
          <select
            value={videoState.playbackSpeed}
            onChange={(e) => setVideoState(prev => ({
              ...prev,
              playbackSpeed: parseFloat(e.target.value)
            }))}
          >
            <option value={0.5}>0.5x</option>
            <option value={1.0}>1.0x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
            <option value={2.0}>2.0x</option>
          </select>
        </div>

        <div className="auto-play-control">
          <label>
            <input
              type="checkbox"
              checked={autoPlay}
              onChange={(e) => setAutoPlay(e.target.checked)}
            />
            Auto-play
          </label>
          {autoPlay && (
            <label className="delay-control">
              Delay:
              <select
                value={autoPlayDelay}
                onChange={(e) => setAutoPlayDelay(parseInt(e.target.value))}
              >
                <option value={0}>No delay</option>
                <option value={500}>0.5s</option>
                <option value={1000}>1s</option>
                <option value={2000}>2s</option>
                <option value={3000}>3s</option>
              </select>
            </label>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
