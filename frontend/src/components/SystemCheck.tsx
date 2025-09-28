import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { env } from '../common/env';
import { Card, CardAction, CardContent, CardTitle } from '../components/ui/card';
import Loading from './SystemCheck/Loading';
import ErrorScreen from './SystemCheck/ErrorScreen';
import { SystemCheckResponse } from '../types/system-check';
import ServiceStatus from './SystemCheck/ServiceStatus';
import { Button } from './ui/button';

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
          navigate('/main');
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred. Please, refresh the page and try again.');
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

  if (loading) {
    return (
      <Loading />
    );
  }

  if (error) {
    return (
      <ErrorScreen error={error} />
    );
  }

  if (!checkStatus) {
    return <ErrorScreen error="The check was not performed. Please, refresh the page and try again." />;
  }

  return (
    <div className="w-full max-w-2xl mx-auto min-h-screen flex items-center justify-center">
      <Card className="w-full">
        <CardContent className="space-y-4">
          <CardTitle>System status: {checkStatus.system_ready ? 'Ready' : 'Not ready'}</CardTitle>

          <div>
            <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">AI CLI Tools</h2>
              <span className={`text-sm ${checkStatus.requirements_met.ai_cli ? 'text-primary' : 'text-destructive'}`}>
                {checkStatus.requirements_met.ai_cli ? 'Available' : 'Not available'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <Card>
                <CardContent>
                  <ServiceStatus name="Claude Code" status={checkStatus.services.claude_code} />
                </CardContent>
              </Card>
              <Card>
                <CardContent>
                  <ServiceStatus name="OpenCode" status={checkStatus.services.opencode} />
                </CardContent>
              </Card>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium">Text-to-Speech Services</h2>
              <span className={`text-sm ${checkStatus.requirements_met.tts_service ? 'text-primary' : 'text-destructive'}`}>
                {checkStatus.requirements_met.tts_service ? 'Available' : 'Not available'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <Card>
                <CardContent>
                  <ServiceStatus name="ElevenLabs" status={checkStatus.services.elevenlabs} />
                </CardContent>
              </Card>
              <Card>
                <CardContent>
                  <ServiceStatus name="OpenAI TTS" status={checkStatus.services.openai_tts} />
                </CardContent>
              </Card>
            </div>
          </div>

          {checkStatus.recommendations.length > 0 && (
            <Card>
              <CardContent>
                <CardTitle>Recommendations</CardTitle>
                <ul className="mt-4 space-y-2 list-disc list-inside text-sm">
                  {checkStatus.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <CardAction>
            {!checkStatus.system_ready && (
            <Button onClick={handleRetry}>
                Re-check system
              </Button>
            )}
            {checkStatus.system_ready && (
              <Button onClick={() => navigate('/main')}>
                Continue to application
              </Button>
            )}
          </CardAction>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemCheck;
