export interface LineRange {
  from?: number;
  to?: number;
  from_line?: number;
  to_line?: number;
  line?: number;
}

export interface TextBlock {
  type: 'text';
  markdown: string;
}

export interface CodeBlock {
  type: 'code';
  file: string;
  relevant_lines: LineRange[];
  markdown: string;
}

export type ScriptBlock = TextBlock | CodeBlock;

export interface ScriptData {
  repository_path: string;
  question: string;
  script: ScriptBlock[];
  audio_files?: string[];
}

export interface VideoState {
  currentBlock: number;
  isPlaying: boolean;
  isPaused: boolean;
  playbackSpeed: number;
  shouldAutoPlay?: boolean;
}

export interface ScriptRequest {
  repository_path: string;
  question: string;
  ai_provider?: string;
  tts_provider?: string;
}

export interface Provider {
  id: string;
  name: string;
}

export interface AvailableProvidersResponse {
  ai_providers: Provider[];
  tts_providers: Provider[];
}

export interface TTSRequest {
  text: string;
}

export interface TTSResponse {
  audio_url: string;
  cache_hit: boolean;
}

export interface CacheStatsResponse {
  cache_size_bytes: number;
  cache_size_mb: number;
  cached_files_count: number;
}
