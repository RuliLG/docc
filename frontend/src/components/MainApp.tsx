import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VideoPlayer from './VideoPlayer';
import { ScriptData } from '../types/script';
import { ApiService } from '../services/api';
import './MainApp.css';
import { env } from '../common/env';
import SystemCheckLoading from './SystemCheck/Loading';
import ErrorScreen from './ErrorScreen';
import { Button } from './ui/button';
import Loading from './Loading';
import TitleH1 from './ui/TitleH1';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Textarea } from './ui/textarea';

function MainApp() {
  const navigate = useNavigate();
  const [scriptData, setScriptData] = useState<ScriptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionFolder, setSessionFolder] = useState<string | null>(null);
  const [repositoryPath, setRepositoryPath] = useState('');
  const [question, setQuestion] = useState('');
  const [systemReady, setSystemReady] = useState<boolean | null>(null);

  useEffect(() => {
    // Check system status on mount
    checkSystemStatus();

    const urlParams = new URLSearchParams(window.location.search);
    const sessionFolderParam = urlParams.get('session');

    if (sessionFolderParam) {
      setSessionFolder(sessionFolderParam);
      loadSessionScript(sessionFolderParam);
    }
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch(`${env.apiUrl}/system-check/quick`);
      const data = await response.json();

      if (!data.system_ready) {
        // Redirect to system check if not ready
        navigate('/');
      } else {
        setSystemReady(true);
      }
    } catch (err) {
      console.error('Failed to check system status:', err);
      // If we can't check, redirect to system check
      navigate('/');
    }
  };

  const loadSessionScript = async (sessionFolder: string) => {
    try {
      setLoading(true);
      setError(null);

      // Load script.json from the session folder
      const response = await fetch(`/sessions/${sessionFolder}/script.json`);

      if (!response.ok) {
        throw new Error(`Failed to load session: ${response.statusText}`);
      }

      const scriptData = await response.json();
      setScriptData(scriptData);
    } catch (err) {
      setError(`Failed to load session script: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!repositoryPath.trim() || !question.trim()) {
      setError('Please provide both repository path and question');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const script = await ApiService.generateScript({
        repository_path: repositoryPath,
        question: question
      });

      setScriptData(script);
    } catch (err) {
      setError(`Failed to generate script: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExit = () => {
    // Reset state to go back to the form
    setScriptData(null);
    setSessionFolder(null);
    setError(null);
    // Clear URL params if any
    if (window.location.search) {
      window.history.pushState({}, document.title, window.location.pathname);
    }
  };

  const handleCheckSystem = () => {
    navigate('/');
  };

  // Wait for system check
  if (systemReady === null) {
    return (
      <SystemCheckLoading />
    );
  }

  if (loading) {
    return (
      <Loading title="Loading script" description="The AI agent is now going through the app and generating the documentation for you. This process may take a few minutes..." />
    );
  }

  if (error) {
    return (
      <ErrorScreen error={error} title="Error">
        <Button onClick={handleCheckSystem}>
          Check System Requirements
        </Button>
      </ErrorScreen>
    );
  }

  if (!scriptData && !sessionFolder) {
    return (
      <div className="max-w-2xl mx-auto min-h-screen flex items-center justify-center flex-col gap-4">
        <div className="flex justify-between items-center w-full">
          <TitleH1>Ask any question about a repository</TitleH1>
          <Button variant='outline' onClick={handleCheckSystem}>
            Check System Status
          </Button>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
          <div className="flex flex-col gap-2 w-full">
            <Label htmlFor="repositoryPath">Repository Path:</Label>
            <Input
              type="text"
              id="repositoryPath"
              value={repositoryPath}
              onChange={(e) => setRepositoryPath(e.target.value)}
              placeholder="/absolute/path/to/repository"
              required
            />
          </div>
          <div className="flex flex-col gap-2 w-full">
            <Label htmlFor='question'>Question:</Label>
            <Textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What would you like to know about this repository?"
              rows={4}
              required
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? 'Generating...' : 'Generate Documentation'}
          </Button>
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </form>
      </div>
    );
  }

  if (!scriptData) {
    return (
      <ErrorScreen error="No script data available" title="Error" />
    );
  }

  return (
    <div>
      <VideoPlayer
        scriptData={scriptData}
        sessionFolder={sessionFolder || undefined}
        onExit={handleExit}
      />
    </div>
  );
}

export default MainApp;
