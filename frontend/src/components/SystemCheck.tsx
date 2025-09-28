import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardAction, CardContent, CardTitle } from '../components/ui/card';
import Loading from './SystemCheck/Loading';
import ErrorScreen from './ErrorScreen';
import ServiceStatus from './SystemCheck/ServiceStatus';
import { Button } from './ui/button';
import { useSystemCheck } from '../hooks/useSystemCheck';
import TitleH2 from './ui/TitleH2';

const SystemCheck: React.FC = () => {
  const navigate = useNavigate();
  const { checkStatus, loading, error, handleRetry } = useSystemCheck();

  if (loading) {
    return (
      <Loading />
    );
  }

  if (error) {
    return (
      <ErrorScreen error={error} title="There was an error checking system requirements" />
    );
  }

  if (!checkStatus) {
    return <ErrorScreen error="The check was not performed. Please, refresh the page and try again." title="There was an error checking system requirements" />;
  }

  return (
    <div className="w-full max-w-2xl mx-auto min-h-screen flex items-center justify-center">
      <Card className="w-full">
        <CardContent className="space-y-4">
          <CardTitle>System status: {checkStatus.system_ready ? 'Ready' : 'Not ready'}</CardTitle>

          <div>
            <div className="flex items-center justify-between">
              <TitleH2>AI CLI Tools</TitleH2>
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
              <TitleH2>Text-to-Speech Services</TitleH2>
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
