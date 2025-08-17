import { ScriptData } from '../types/script';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface ScriptRequest {
  repository_path: string;
  question: string;
}

export interface TTSRequest {
  text: string;
  voice?: string;
}

export interface TTSResponse {
  audio_url: string;
  cache_hit: boolean;
}

export interface VoicesResponse {
  voices: string[];
  provider: string;
}

export interface CacheStatsResponse {
  cache_size_bytes: number;
  cache_size_mb: number;
  cached_files_count: number;
}

export class ApiService {
  static async generateScript(request: ScriptRequest): Promise<ScriptData> {
    const response = await fetch(`${API_BASE_URL}/generate-script`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate script: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      repository_path: request.repository_path,
      question: request.question,
      script: data.script,
      audio_files: data.audio_files
    };
  }

  static async generateAudio(request: TTSRequest): Promise<TTSResponse> {
    const response = await fetch(`${API_BASE_URL}/generate-audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate audio: ${response.statusText}`);
    }

    return response.json();
  }

  static async getAudioUrl(audioId: string): Promise<string> {
    return `${API_BASE_URL}/audio/${audioId}`;
  }

  static async getVoices(): Promise<VoicesResponse> {
    const response = await fetch(`${API_BASE_URL}/voices`);

    if (!response.ok) {
      throw new Error(`Failed to get voices: ${response.statusText}`);
    }

    return response.json();
  }

  static async getCacheStats(): Promise<CacheStatsResponse> {
    const response = await fetch(`${API_BASE_URL}/cache/stats`);

    if (!response.ok) {
      throw new Error(`Failed to get cache stats: ${response.statusText}`);
    }

    return response.json();
  }

  static async clearCache(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/cache`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to clear cache: ${response.statusText}`);
    }
  }

  static async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }
}