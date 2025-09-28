
export interface ServiceStatus {
  installed?: boolean;
  configured?: boolean;
  accessible?: boolean;
  version?: string | null;
  error?: string | null;
  api_key_set?: boolean;
}

export interface SystemCheckResponse {
  system_ready: boolean;
  requirements_met: {
    ai_cli: boolean;
    tts_service: boolean;
  };
  services: {
    claude_code: ServiceStatus;
    opencode: ServiceStatus;
    elevenlabs: ServiceStatus;
    openai_tts: ServiceStatus;
  };
  recommendations: string[];
}
