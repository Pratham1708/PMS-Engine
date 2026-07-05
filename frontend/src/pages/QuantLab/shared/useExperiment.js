import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom React hook to manage polling for async quant experiments.
 *
 * @param {Function} startFn - API function to trigger the experiment. Returns {data: {experiment_id: '...'}}
 * @param {Function} statusFn - API function to poll status. Expects ID, returns {data: {status: 'complete'|'failed'|'running'|'pending', error_msg: '...'}}
 * @param {Function} resultFn - API function to retrieve final details. Expects ID, returns {data: {...}}
 */
export default function useExperiment(startFn, statusFn, resultFn) {
  const [status, setStatus] = useState('idle'); // idle, pending, running, complete, failed
  const [experimentId, setExperimentId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  const cleanUp = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
  }, []);

  const run = async (payload) => {
    cleanUp();
    setStatus('pending');
    setResult(null);
    setError(null);
    setElapsedTime(0);

    try {
      const startRes = await startFn(payload);
      const expId = startRes.data?.experiment_id;

      if (!expId) {
        throw new Error('No experiment_id returned from execution api');
      }

      setExperimentId(expId);
      setStatus('running');

      // Start elapsed timer
      timerIntervalRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);

      // Start status polling
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusRes = await statusFn(expId);
          const currentStatus = statusRes.data?.status;
          const errMsg = statusRes.data?.error_msg;

          if (currentStatus === 'complete') {
            cleanUp();
            const resultRes = await resultFn(expId);
            setResult(resultRes.data);
            setStatus('complete');
          } else if (currentStatus === 'failed') {
            cleanUp();
            setError(errMsg || 'Experiment execution failed.');
            setStatus('failed');
          }
        } catch (pollErr) {
          console.error('Error polling experiment status:', pollErr);
        }
      }, 2000);

    } catch (err) {
      cleanUp();
      setError(err.response?.data?.detail || err.message || 'Failed to start experiment.');
      setStatus('failed');
    }
  };

  const reset = () => {
    cleanUp();
    setStatus('idle');
    setExperimentId(null);
    setResult(null);
    setError(null);
    setElapsedTime(0);
  };

  useEffect(() => {
    return () => cleanUp();
  }, [cleanUp]);

  return {
    run,
    reset,
    status,
    experimentId,
    result,
    error,
    elapsedTime,
  };
}

