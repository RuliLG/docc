import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { env } from '../common/env';
import TitleH1 from '../shadcn-components/TitleH1';
import { Card, CardTitle } from '../components/ui/card';

interface ServiceStatus {
  installed?: boolean;
  configured?: boolean;
  accessible?: boolean;
  version?: string | null;
  error?: string | null;
  api_key_set?: boolean;
}

interface SystemCheckResponse {
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

const SystemCheck: React.FC = () => {
  const navigate = useNavigate();
  const [checkStatus, setCheckStatus] = useState<SystemCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const performSystemCheck = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${env.apiUrl}/system-check`);

      if (!response.ok) {
        throw new Error(`System check failed: ${response.statusText}`);
      }

      const data: SystemCheckResponse = await response.json();
      setCheckStatus(data);

      if (data.system_ready) {
        setTimeout(() => {
          // navigate('/main');
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    performSystemCheck();
  }, [retryCount]);

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
  };

  const renderServiceStatus = (name: string, status: ServiceStatus) => {
    const isConfigured = status.configured || status.accessible;
    const hasError = status.error && !isConfigured;

    return (
      <div className={`service-item ${isConfigured ? 'success' : hasError ? 'error' : 'warning'}`}>
        <div className="service-header">
          <span className="service-name">{name}</span>
          <span className={`status-icon ${isConfigured ? 'success' : 'error'}`}>
            {isConfigured ? '✓' : '✗'}
          </span>
        </div>
        <div className="service-details">
          {status.version && (
            <div className="detail-item">
              <span className="detail-label">Version:</span>
              <span className="detail-value">{status.version}</span>
            </div>
          )}
          {status.installed !== undefined && (
            <div className="detail-item">
              <span className="detail-label">Installed:</span>
              <span className={`detail-value ${status.installed ? 'success' : 'error'}`}>
                {status.installed ? 'Yes' : 'No'}
              </span>
            </div>
          )}
          {status.configured !== undefined && (
            <div className="detail-item">
              <span className="detail-label">Configured:</span>
              <span className={`detail-value ${status.configured ? 'success' : 'error'}`}>
                {status.configured ? 'Yes' : 'No'}
              </span>
            </div>
          )}
          {status.api_key_set !== undefined && (
            <div className="detail-item">
              <span className="detail-label">API Key:</span>
              <span className={`detail-value ${status.api_key_set ? 'success' : 'error'}`}>
                {status.api_key_set ? 'Set' : 'Not Set'}
              </span>
            </div>
          )}
          {status.accessible !== undefined && (
            <div className="detail-item">
              <span className="detail-label">Accessible:</span>
              <span className={`detail-value ${status.accessible ? 'success' : 'error'}`}>
                {status.accessible ? 'Yes' : 'No'}
              </span>
            </div>
          )}
          {status.error && (
            <div className="error-message">
              {status.error}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="system-check-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <h2>Checking System Requirements...</h2>
          <p>Validating AI CLI tools and TTS services</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="system-check-container">
        <div className="error-container">
          <h2>System Check Failed</h2>
          <p className="error-message">{error}</p>
          <button onClick={handleRetry} className="retry-button">
            Retry System Check
          </button>
        </div>
      </div>
    );
  }

  if (!checkStatus) {
    return null;
  }

  return (
    <Card>
      <CardTitle>System Requirements Check</CardTitle>

      <div className={`overall-status ${checkStatus.system_ready ? 'ready' : 'not-ready'}`}>
        <div className="status-header">
          <span className="status-text">
            System Status: {checkStatus.system_ready ? 'Ready' : 'Not Ready'}
          </span>
          <span className={`status-icon ${checkStatus.system_ready ? 'success' : 'error'}`}>
            {checkStatus.system_ready ? '✓' : '✗'}
          </span>
        </div>
        {checkStatus.system_ready && (
          <p className="ready-message">All requirements met! Redirecting to application...</p>
        )}
      </div>

      <div className="requirements-section">
        <h2>AI CLI Tools</h2>
        <div className="requirement-status">
          <span>Status:</span>
          <span className={`status ${checkStatus.requirements_met.ai_cli ? 'success' : 'error'}`}>
            {checkStatus.requirements_met.ai_cli ? 'Available' : 'Not Available'}
          </span>
        </div>
        <div className="services-grid">
          {renderServiceStatus('Claude Code', checkStatus.services.claude_code)}
          {renderServiceStatus('OpenCode', checkStatus.services.opencode)}
        </div>
      </div>

      <div className="requirements-section">
        <h2>Text-to-Speech Services</h2>
        <div className="requirement-status">
          <span>Status:</span>
          <span className={`status ${checkStatus.requirements_met.tts_service ? 'success' : 'error'}`}>
            {checkStatus.requirements_met.tts_service ? 'Available' : 'Not Available'}
          </span>
        </div>
        <div className="services-grid">
          {renderServiceStatus('ElevenLabs', checkStatus.services.elevenlabs)}
          {renderServiceStatus('OpenAI TTS', checkStatus.services.openai_tts)}
        </div>
      </div>

      {checkStatus.recommendations.length > 0 && (
        <div className="recommendations-section">
          <h2>Recommendations</h2>
          <ul className="recommendations-list">
            {checkStatus.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="actions-section">
        {!checkStatus.system_ready && (
          <button onClick={handleRetry} className="retry-button">
            Re-check System
          </button>
        )}
        {checkStatus.system_ready && (
          <button onClick={() => navigate('/main')} className="continue-button">
            Continue to Application
          </button>
        )}
      </div>
    </Card>
  );
};

export default SystemCheck;
