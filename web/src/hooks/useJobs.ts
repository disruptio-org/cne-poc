import { useCallback, useEffect, useState } from 'react';
import axios from '../api';

export interface JobSummary {
  job_id: string;
  status: string;
  filename: string;
  created_at: string;
  updated_at: string;
  error?: string | null;
  ocr_conf_mean?: number | null;
}

export interface JobDetail extends JobSummary {
  preview_ready: boolean;
  csv_ready: boolean;
  metadata: Record<string, unknown>;
}

const useJobs = () => {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get<{ jobs: JobSummary[] }>('/jobs/');
      setJobs(response.data.jobs);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { jobs, loading, refresh };
};

export default useJobs;
