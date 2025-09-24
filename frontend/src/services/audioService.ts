import { env } from '../common/env';
import { ApiService } from './api';

let API_BASE_URL = env.apiUrl;
if (API_BASE_URL?.includes('/api/v1')) {
  API_BASE_URL = API_BASE_URL.substring(0, API_BASE_URL.indexOf('/api/v1'));
}

export class AudioService {
  private audioCache: Map<string, HTMLAudioElement> = new Map();
  private currentAudio: HTMLAudioElement | null = null;
  private sessionFolder: string | null = null;

  setSessionFolder(sessionFolder: string): void {
    this.sessionFolder = sessionFolder;
    this.clearCache(); // Clear cache when switching sessions
  }

  async loadAudioFromSession(audioFileName: string): Promise<HTMLAudioElement> {
    if (!this.sessionFolder) {
      throw new Error('No session folder set');
    }

    // Check if audio is already cached
    if (this.audioCache.has(audioFileName)) {
      return this.audioCache.get(audioFileName)!;
    }

    try {
      // Load audio file from session folder
      const audioUrl = `/sessions/${this.sessionFolder}/audio/${audioFileName}`;

      // Create audio element
      const audio = new Audio(audioUrl);
      audio.preload = 'auto';

      // Cache the audio
      this.audioCache.set(audioFileName, audio);

      return audio;
    } catch (error) {
      console.error('Failed to load audio:', error);
      throw error;
    }
  }

  async generateAndCacheAudio(text: string): Promise<HTMLAudioElement> {
    const cacheKey = text;

    // Check if audio is already cached
    if (this.audioCache.has(cacheKey)) {
      return this.audioCache.get(cacheKey)!;
    }

    try {
      // Generate audio via API (fallback for when no session is available)
      const ttsResponse = await ApiService.generateAudio({ text });

      // Extract audio ID from URL
      const audioId = ttsResponse.audio_url.split('/').pop()!;
      const fullAudioUrl = await ApiService.getAudioUrl(audioId);

      // Create audio element
      const audio = new Audio(fullAudioUrl);
      audio.preload = 'auto';

      // Cache the audio
      this.audioCache.set(cacheKey, audio);

      return audio;
    } catch (error) {
      console.error('Failed to generate audio:', error);
      throw error;
    }
  }

  async playAudioFromUrl(audioUrl: string, playbackSpeed: number = 1.0): Promise<void> {
    try {
      // Stop current audio if playing
      this.stopCurrentAudio();

      // Convert relative URL to absolute URL if needed
      const fullAudioUrl = audioUrl.startsWith('http')
        ? audioUrl
        : `${API_BASE_URL}${audioUrl}`;

      console.log('Playing audio from URL:', fullAudioUrl);

      // Check if audio is already cached
      if (this.audioCache.has(fullAudioUrl)) {
        const audio = this.audioCache.get(fullAudioUrl)!;
        audio.playbackRate = playbackSpeed;
        this.currentAudio = audio;
      } else {
        const audio = new Audio(fullAudioUrl);
        audio.preload = 'auto';
        audio.playbackRate = playbackSpeed;

        // Add more detailed error handling
        audio.addEventListener('loadedmetadata', () => {
          console.log(`Audio loaded successfully: duration=${audio.duration}s`);
        });

        audio.addEventListener('error', (e) => {
          console.error('Audio element error event:', e);
          const audioError = audio.error;
          if (audioError) {
            console.error(`Audio error code: ${audioError.code}, message: ${audioError.message}`);
          }
        });

        // Cache the audio
        this.audioCache.set(fullAudioUrl, audio);
        this.currentAudio = audio;
      }

      return new Promise((resolve, reject) => {
        this.currentAudio!.onended = () => {
          this.currentAudio = null;
          resolve();
        };

        this.currentAudio!.onerror = (e) => {
          console.error('Audio playback error:', e);
          console.error('Failed to load audio from:', fullAudioUrl);
          this.currentAudio = null;
          reject(new Error('Audio playback failed'));
        };

        this.currentAudio!.play().catch(reject);
      });
    } catch (error) {
      throw new Error(`Failed to play audio from URL: ${error}`);
    }
  }

  async playAudioFromSession(audioFileName: string, playbackSpeed: number = 1.0): Promise<void> {
    try {
      // Stop current audio if playing
      this.stopCurrentAudio();

      const audio = await this.loadAudioFromSession(audioFileName);
      audio.playbackRate = playbackSpeed;

      this.currentAudio = audio;

      return new Promise((resolve, reject) => {
        audio.onended = () => {
          this.currentAudio = null;
          resolve();
        };

        audio.onerror = () => {
          this.currentAudio = null;
          reject(new Error('Audio playback failed'));
        };

        audio.play().catch(reject);
      });
    } catch (error) {
      throw new Error(`Failed to play session audio: ${error}`);
    }
  }

  async playAudio(text: string, playbackSpeed: number = 1.0): Promise<void> {
    try {
      // Stop current audio if playing
      this.stopCurrentAudio();

      const audio = await this.generateAndCacheAudio(text);
      audio.playbackRate = playbackSpeed;

      this.currentAudio = audio;

      return new Promise((resolve, reject) => {
        audio.onended = () => {
          this.currentAudio = null;
          resolve();
        };

        audio.onerror = () => {
          this.currentAudio = null;
          reject(new Error('Audio playback failed'));
        };

        audio.play().catch(reject);
      });
    } catch (error) {
      throw new Error(`Failed to play audio: ${error}`);
    }
  }

  pauseCurrentAudio(): void {
    if (this.currentAudio && !this.currentAudio.paused) {
      this.currentAudio.pause();
    }
  }

  resumeCurrentAudio(): void {
    if (this.currentAudio && this.currentAudio.paused) {
      this.currentAudio.play().catch(console.error);
    }
  }

  stopCurrentAudio(): void {
    if (this.currentAudio) {
      console.log('Stopping current audio');
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
  }

  setPlaybackSpeed(speed: number): void {
    if (this.currentAudio) {
      this.currentAudio.playbackRate = speed;
    }
  }

  isPlaying(): boolean {
    return this.currentAudio ? !this.currentAudio.paused : false;
  }

  getCurrentTime(): number {
    return this.currentAudio ? this.currentAudio.currentTime : 0;
  }

  getDuration(): number {
    return this.currentAudio ? this.currentAudio.duration : 0;
  }

  clearCache(): void {
    this.stopCurrentAudio();
    this.audioCache.clear();
  }

  getCacheSize(): number {
    return this.audioCache.size;
  }
}
