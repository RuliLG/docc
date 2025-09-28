import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { env } from '../common/env';
import { SystemCheckResponse } from '../types/system-check';

export const useSystemCheck = () => {
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

  return {
    checkStatus,
    loading,
    error,
    handleRetry,
  };
};