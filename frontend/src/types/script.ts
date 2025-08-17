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