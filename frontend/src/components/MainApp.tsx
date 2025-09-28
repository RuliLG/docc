import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VideoPlayer from './VideoPlayer';
import { ScriptData } from '../types/script';
import { ApiService } from '../services/api';
import './MainApp.css';
import { env } from '../common/env';

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
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Checking system status...</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="App loading">
        <div className="loading-spinner"></div>
        <p>Loading script...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="App error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={handleCheckSystem} className="system-check-button">
          Check System Requirements
        </button>
      </div>
    );
  }

  if (!scriptData && !sessionFolder) {
    return (
      <div className="App">
        <div className="form-container">
          <h1>Documentation Generator</h1>
          <button onClick={handleCheckSystem} className="system-status-button">
            Check System Status
          </button>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="repositoryPath">Repository Path:</label>
              <input
                type="text"
                id="repositoryPath"
                value={repositoryPath}
                onChange={(e) => setRepositoryPath(e.target.value)}
                placeholder="/path/to/repository"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="question">Question:</label>
              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What would you like to know about this repository?"
                rows={4}
                required
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Generating...' : 'Generate Documentation'}
            </button>
            {error && <div className="error-message">{error}</div>}
          </form>
        </div>
      </div>
    );
  }

  if (!scriptData) {
    return (
      <div className="App error">
        <h2>No Script Data</h2>
        <p>No script data available</p>
      </div>
    );
  }

  return (
    <div className="App">
      <VideoPlayer
        scriptData={scriptData}
        sessionFolder={sessionFolder || undefined}
        onExit={handleExit}
      />
    </div>
  );
}

export default MainApp;
