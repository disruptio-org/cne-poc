import { useEffect, useState } from 'react';

import useJobs from '../hooks/useJobs';
import axios from '../api';

interface ModelMetadata {
  model_name: string;
  version: string;
  created_at: string;
  status: string;
  metrics: Record<string, unknown>;
}

const HistoryPage = () => {
  const { jobs, refresh } = useJobs();
  const [models, setModels] = useState<ModelMetadata[]>([]);

  useEffect(() => {
    refresh();
    const loadModels = async () => {
      const response = await axios.get<{ items: ModelMetadata[] }>('/models/history');
      setModels(response.data.items);
    };
    loadModels();
  }, [refresh]);

  return (
    <div className="history-page">
      <div className="card">
        <h2>Jobs aprovados</h2>
        <ul>
          {jobs
            .filter((job) => job.status === 'approved')
            .map((job) => (
              <li key={job.job_id}>
                {job.filename} - {job.status} em {new Date(job.updated_at).toLocaleString()}
              </li>
            ))}
        </ul>
      </div>
      <div className="card">
        <h2>Histórico de modelos</h2>
        <ul>
          {models.map((model) => (
            <li key={model.version}>
              {model.model_name} v{model.version} - {model.status} -{' '}
              {JSON.stringify(model.metrics)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default HistoryPage;
