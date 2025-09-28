import { env } from '../common/env';
import { AvailableProvidersResponse, CacheStatsResponse, ScriptData, ScriptRequest, TTSRequest, TTSResponse } from '../types/script';

export class ApiService {
  static async generateScript(request: ScriptRequest): Promise<ScriptData> {
    const response = await fetch(`${env.apiUrl}/generate-script`, {
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
    const response = await fetch(`${env.apiUrl}/generate-audio`, {
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
    return `${env.apiUrl}/audio/${audioId}`;
  }

  static async getCacheStats(): Promise<CacheStatsResponse> {
    const response = await fetch(`${env.apiUrl}/cache/stats`);

    if (!response.ok) {
      throw new Error(`Failed to get cache stats: ${response.statusText}`);
    }

    return response.json();
  }

  static async clearCache(): Promise<void> {
    const response = await fetch(`${env.apiUrl}/cache`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to clear cache: ${response.statusText}`);
    }
  }

  static async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${env.apiUrl}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async getAvailableProviders(): Promise<AvailableProvidersResponse> {
    const response = await fetch(`${env.apiUrl}/available-providers`);

    if (!response.ok) {
      throw new Error(`Failed to get available providers: ${response.statusText}`);
    }

    return response.json();
  }
}
