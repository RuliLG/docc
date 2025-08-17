import React, { useState, useEffect } from 'react';
import VideoPlayer from './components/VideoPlayer';
import { ScriptData } from './types/script';
import { ApiService } from './services/api';
import './App.css';

function App() {
  const [scriptData, setScriptData] = useState<ScriptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionFolder, setSessionFolder] = useState<string | null>(null);
  const [repositoryPath, setRepositoryPath] = useState('');
  const [question, setQuestion] = useState('');

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionFolderParam = urlParams.get('session');

    if (sessionFolderParam) {
      setSessionFolder(sessionFolderParam);
      loadSessionScript(sessionFolderParam);
    }
  }, []);

  const loadSessionScript = async (sessionFolder: string) => {
    try {
      setLoading(true);
      setError(null);

      // Load script.json from the session folder
      // For local development, we'll need to serve the sessions folder
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
      </div>
    );
  }

  if (!scriptData && !sessionFolder) {
    return (
      <div className="App">
        <div className="form-container">
          <h1>Documentation Generator</h1>
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
      <VideoPlayer scriptData={scriptData} sessionFolder={sessionFolder || undefined} />
    </div>
  );
}

export default App;
